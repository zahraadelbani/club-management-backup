from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import ChatRoom, Message, DirectChatRoom, DirectMessage
from polls.models import Poll, Choice, PollVote
from clubs.models import Club
from users.models import Membership
from collections import defaultdict
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from messaging.utils import can_initiate_direct_chat
from django.contrib.auth import get_user_model
User = get_user_model()

@login_required
def group_chat(request, room_slug):
    room = get_object_or_404(ChatRoom, slug=room_slug)
    messages_qs = Message.objects.filter(room=room).select_related("poll").prefetch_related("poll__choices").order_by("timestamp")

    # Attach vote status per message
    for msg in messages_qs:
        if msg.message_type == "poll" and msg.poll:
            vote = PollVote.objects.filter(user=request.user, poll=msg.poll).first()
            msg.has_voted = vote is not None
            msg.selected_choice_id = vote.choice.id if vote else None
            msg.total_votes = msg.poll.poll_votes.count()
            for choice in msg.poll.choices.all():
                choice.vote_count = choice.pollvote_set.count()
                choice.vote_percent = (choice.vote_count / msg.total_votes * 100) if msg.total_votes else 0
    # Ensure user is a member or leader of this club
    membership = Membership.objects.filter(
        user=request.user,
        club=room.club,
        membership_type__in=["member", "leader"]
    ).first()

    if not membership:
        messages.error(request, _("You are not a member of this club."))
        return redirect("home")

    polls = Poll.objects.filter(club=room.club, is_active=True).order_by("-created_at")

    # Handle POST actions
    if request.method == "POST":
        if "create_poll" in request.POST:
            if membership.membership_type == "leader":
                question = request.POST.get("question")
                choices = request.POST.getlist("choices[]")
                if question and choices:
                    poll = Poll.objects.create(
                        club=room.club,
                        question=question,
                        created_by=request.user,
                        is_active=True,
                    )
                    for choice_text in choices:
                        if choice_text.strip():
                            Choice.objects.create(poll=poll, text=choice_text.strip())
                    messages.success(request, _("Poll created successfully."))
                    return redirect("messaging:group_chat", room_slug=room.slug)
                else:
                    messages.error(request, _("Poll question and choices are required."))

        elif "vote_poll" in request.POST:
            poll_id = request.POST.get("poll_id")
            choice_id = request.POST.get("choice_id")
            poll = get_object_or_404(Poll, id=poll_id, club=room.club)
            choice = get_object_or_404(Choice, id=choice_id, poll=poll)

            already_voted = PollVote.objects.filter(poll=poll, user=request.user).exists()
            if not already_voted:
                PollVote.objects.create(poll=poll, choice=choice, user=request.user)
                messages.success(request, _("Vote submitted successfully."))
            else:
                messages.warning(request, _("You have already voted on this poll."))

            return redirect("messaging:group_chat", room_slug=room.slug)

    # Precompute vote status and selected choice
    polls_with_vote_status = []
    for poll in polls:
        vote = PollVote.objects.filter(user=request.user, poll=poll).first()
        has_voted = vote is not None
        selected_choice_id = vote.choice.id if vote else None
        polls_with_vote_status.append((poll, has_voted, selected_choice_id))

    return render(request, "messaging/group_chat.html", {
        "room": room,
        "club": room.club,
        "chat_messages": messages_qs,
        "polls_with_vote_status": polls_with_vote_status,
        "membership": membership,
        "room_slug": room.slug, 
    })

@login_required
def messaging_rooms(request):
    user = request.user
    is_aca = user.role == "activity_center_admin"

    user_clubs = Club.objects.filter(
        memberships__user=user,
        memberships__membership_type__in=["member", "leader"]
    ).distinct()

    chat_rooms = ChatRoom.objects.filter(club__in=user_clubs)

    dm_users = set()
    user_club_map = defaultdict(set)

    all_other_users = User.objects.exclude(id=user.id)

    for other_user in all_other_users:
        if not can_initiate_direct_chat(user, other_user):
            continue

        dm_users.add(other_user)

        if is_aca:
            # Show clubs the user is a leader of
            leader_clubs = Club.objects.filter(
                memberships__user=other_user,
                memberships__membership_type="leader"
            ).values_list("name", flat=True)
            user_club_map[other_user.id] = list(leader_clubs)
        else:
            # Show only shared clubs (for filtering)
            shared_clubs = Club.objects.filter(
                memberships__user=user,
                memberships__membership_type__in=["member", "leader"],
                memberships__club__memberships__user=other_user
            ).distinct()

            for club in shared_clubs:
                user_club_map[other_user.id].add(club.name)

    # Convert sets to sorted lists
    user_club_map = {uid: sorted(list(clubs)) for uid, clubs in user_club_map.items()}

    return render(request, "messaging/messaging_rooms.html", {
        "chat_rooms": chat_rooms,
        "dm_users": dm_users,
        "user_club_map": user_club_map,
        "user_clubs": user_clubs,
        "is_aca": is_aca,
        "current_user_id": user.id,
    })


@login_required
@require_GET
def get_direct_chat_history(request, user_id):
    from_user = request.user
    to_user_id = int(user_id)
    other_user = get_object_or_404(User, id=to_user_id)

    if not can_initiate_direct_chat(from_user, other_user):
        return JsonResponse({"error": "Not authorized"}, status=403)

    room, _ = DirectChatRoom.get_or_create_between_users(from_user, other_user)
    messages = DirectMessage.objects.filter(room=room).select_related("sender").order_by("timestamp")

    data = [{
        "sender_id": msg.sender.id,
        "sender": msg.sender.name,
        "profile_picture": msg.sender.profile_picture.url if msg.sender.profile_picture else "",
        "timestamp": msg.timestamp.strftime("%H:%M"),
        "message": msg.content
    } for msg in messages]

    return JsonResponse({"messages": data})