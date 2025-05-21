from datetime import timedelta
from django.contrib import messages as django_messages
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.translation import gettext as _
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from threading import Timer
from django.utils.timezone import now
from django.db.models import Q
from notifications.utils import create_notification
from reminders.models import EventReminder
from voting.models import Election
from .models import MembershipTerminationRequest
from clubs.models import Announcement, Club, ClubDocument, Event, EventAttendance
from feedback.models import Feedback
from users.models import User, Membership
from django.core.mail import send_mail
from django.utils import timezone
from threading import Timer
from clubs.models import Event
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.urls import reverse


@login_required
def dashboard(request):
    user = request.user

    member_clubs = Club.objects.filter(
        memberships__user=user,
        memberships__membership_type="member"
    )

    joined_club_ids = member_clubs.values_list("id", flat=True)

    available_clubs = [
        club for club in Club.objects.exclude(id__in=joined_club_ids)
        if club.has_quota() and Membership.objects.filter(user=user).count() < 3
    ]

    upcoming_events = Event.objects.filter(
        club__in=member_clubs,
        approval_status="approved"
    ).select_related("club").order_by("event_date")

    termination_requests = MembershipTerminationRequest.objects.filter(
        membership__user=user,
        status="pending"
    )

    context = {
        "member_clubs": member_clubs,
        "upcoming_events": upcoming_events,
        "termination_requests": termination_requests,
        "available_clubs": available_clubs,
        "election_class": Election, 

    }

    return render(request, "club_member/dashboard.html", context)


@login_required
def join_club(request):
    user = request.user
    total_memberships = Membership.objects.filter(user=user).count()

    if request.method == "POST":
        club_id = request.POST.get("club_id")
        club = get_object_or_404(Club, id=club_id)

        if Membership.objects.filter(user=user, club=club).exists():
            messages.error(request, _("You already have a membership (of any type) with this club."))
            return redirect("club_member:dashboard")

        if total_memberships >= 3:
            messages.error(request, _("You cannot have more than 3 total memberships (including pending ones)."))
            return redirect("club_member:dashboard")

        if not club.has_quota():
            messages.error(request, _("This club has reached its member quota."))
            return redirect("club_member:dashboard")

        # Create as a pending request
        Membership.objects.create(user=user, club=club, membership_type="pending")
        messages.success(request, _(f"Your request to join {club.name} has been submitted."))

        # Notify club leader
        leader = club.leader()
        if leader:
            create_notification(
                user=leader,
                title="New Membership Request",
                message=f"{user.name} has requested to join {club.name}.",
                url=reverse("club_leader:club_members"),
            )

    return redirect("club_member:dashboard")

@login_required
def leave_club(request, club_id):
    user = request.user
    membership = get_object_or_404(Membership, user=user, club_id=club_id, membership_type="member")

    existing_request = MembershipTerminationRequest.objects.filter(
        membership=membership,
        status="pending"
    ).exists()

    if existing_request:
        messages.error(request, _("You already have a pending request to leave this club."))
    else:
        MembershipTerminationRequest.objects.create(
            membership=membership,
            club=membership.club
        )
        messages.success(request, _("Your request to leave has been submitted."))

        # Notify the club leader
        leader = membership.club.leader()
        if leader:
            create_notification(
                user=leader,
                title=" Termination Request Submitted",
                message=f"{user.name} has requested to leave {membership.club.name}.",
                url=reverse("club_leader:club_members"), 
            )

    return redirect("club_member:dashboard")



@login_required
def view_documents(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    documents = ClubDocument.objects.filter(club=club)
    return render(request, "club_member/documents.html", {"club": club, "documents": documents})


@login_required
def view_events(request):
    user = request.user
    two_weeks_ago = timezone.now() - timedelta(days=14)

    member_clubs = Club.objects.filter(
        memberships__user=user, 
        memberships__membership_type="member"
    )

    events = Event.objects.filter(
        approval_status="approved",
        event_date__gte=two_weeks_ago  # Only upcoming and recent past events
    ).filter(
        Q(club__in=member_clubs) | Q(club__isnull=True)
    ).order_by("event_date")

    return render(request, "club_member/events.html", {"events": events})
@login_required
def cancel_termination_request(request, request_id):
    termination_request = get_object_or_404(MembershipTerminationRequest, id=request_id, membership__user=request.user)

    if termination_request.status == "pending":
        termination_request.delete()
        messages.success(request, _("Your membership termination request has been canceled."))
    else:
        messages.error(request, _("You can only cancel pending termination requests."))

    return redirect("club_member:dashboard")

@login_required
def event_calendar_member(request):
    # All clubs where the user is a member
    clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__membership_type="member"
    )

    if not clubs.exists():
        return HttpResponseForbidden(_("You're not a member of any clubs."))

    # Get approved, upcoming events either from the member's clubs or ACA
    events = Event.objects.filter(
        approval_status="approved",
        event_date__gte=timezone.now()
    ).filter(
        Q(club__in=clubs) | Q(club__isnull=True)
    ).select_related("club").order_by("event_date")[:3]  # ✅ limit to 4

    # Event IDs the user has already set reminders for
    reminded_event_ids = EventReminder.objects.filter(
        user=request.user,
        event__in=events
    ).values_list("event_id", flat=True)

    return render(request, "club_member/calendar.html", {
        "events": events,
        "reminders": reminded_event_ids,
        "clubs": clubs,
        "reminded_event_ids": list(reminded_event_ids),
        "clubs": clubs
    })

@login_required
def get_events_member(request):
    clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__membership_type="member"
    )

    # Only show approved, upcoming events from member's clubs or ACA
    approved_events = Event.objects.filter(
        approval_status="approved",
        event_date__gte=timezone.now()
    ).filter(
        Q(club__in=clubs) | Q(club__isnull=True)
    ).select_related("club")

    data = [
        {
            "title": f"{event.title} ({event.club.name if event.club else 'ACA'})",
            "start": event.event_date.isoformat(),
            "approval_status": event.approval_status,
        }
        for event in approved_events
    ]

    return JsonResponse(data, safe=False)

@login_required
def remind_me(request, event_id):
    event = get_object_or_404(Event, id=event_id, approval_status="approved")

    if request.method == "POST":
        user = request.user

        if EventReminder.objects.filter(user=user, event=event).exists():
            messages.warning(request, _("You've already requested a reminder for this event."))
            return redirect("club_member:event_calendar")

        scheduled_for = timezone.now() + timezone.timedelta(minutes=1)

        EventReminder.objects.create(
            user=user,
            event=event,
            scheduled_for=scheduled_for,
        )

        def send_reminder():
            subject = _(f"Reminder: {event.title}")
            from_email = "no-reply@activitycenter.com"
            to = [user.email]

            text_content = (
                f"{_('Hello')} {user.name},\n\n"
                f"{event.title} {_('is happening on')} {event.event_date.strftime('%A, %B %d at %I:%M %p')}.\n\n"
                f"{_('Club')}: {event.club.name}\n"
                f"{_('Created by')}: {event.created_by.name if event.created_by else 'N/A'}\n\n"
                f"- {_('Activity Center')}"
            )

            image_url = request.build_absolute_uri(event.image.url) if event.image else None 


            html_content = render_to_string("emails/event_reminder.html", {
                "user": user,
                "event": event,
                "image_url": image_url,
            })

            msg = EmailMultiAlternatives(subject, text_content, from_email, to)
            msg.attach_alternative(html_content, "text/html")
            msg.send()

        Timer(60, send_reminder).start()

        messages.success(request, _(f"You'll be reminded about \"{event.title}\" in 1 minute."))
        return redirect("club_member:event_calendar")


@login_required
def member_announcements(request):
    user = request.user

    user_clubs = Club.objects.filter(
        memberships__user=user,
        memberships__membership_type="member"
    ).distinct()

    selected_club_id = request.GET.get("club")

    if selected_club_id == "global":
        announcements_qs = Announcement.objects.filter(
            visible=True,
            club__isnull=True
        )
    elif selected_club_id:
        announcements_qs = Announcement.objects.filter(
            visible=True,
            club__id=selected_club_id
        ).distinct()
    else:
        announcements_qs = Announcement.objects.filter(
            visible=True
        ).filter(
            Q(club__isnull=True) | Q(club__in=user_clubs)
        ).distinct()

    announcements_qs = announcements_qs.order_by("-created_at")

    # Paginate
    paginator = Paginator(announcements_qs, 6)  # Show 6 per page
    page_number = request.GET.get("page")
    announcements = paginator.get_page(page_number)

    return render(request, "club_member/member_announcements.html", {
        "announcements": announcements,
        "user_clubs": user_clubs
    })


@login_required
def contact(request):
    if not request.user.is_authenticated:
        return redirect('account_login')

    member_clubs = Club.objects.filter(
        memberships__user=request.user,
        memberships__membership_type='member'
    ).distinct()

    leaders = []
    for club in member_clubs:
        leader_membership = club.memberships.filter(membership_type='leader').first()
        if leader_membership:
            leaders.append({
                'club': club,
                'leader': leader_membership.user,
            })

    return render(request, 'club_member/contact.html', {'leaders': leaders})


@login_required
def faq_user_member(request):
    return render(request, 'club_member/faq_user_member.html')


@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    user = request.user

    attendance_record = EventAttendance.objects.filter(user=user, event=event).first()

    if request.method == "POST":
        if attendance_record and attendance_record.is_attending:
            attendance_record.is_attending = False
            attendance_record.save()
            messages.info(request, _("Your RSVP has been cancelled."))
        else:
            if attendance_record:
                attendance_record.is_attending = True
                attendance_record.save()
            else:
                EventAttendance.objects.create(user=user, event=event, is_attending=True)
            messages.success(request, _("You've RSVP'd to this event."))

        return redirect("club_member:event_detail", event_id=event_id)

    return render(request, "club_member/event_detail.html", {
        "event": event,
        "attendance_record": attendance_record,
    })

@login_required
def qr_attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id, approval_status="approved")
    user = request.user

    attendance, _ = EventAttendance.objects.get_or_create(user=user, event=event)

    if not attendance.is_attending:
        django_messages.warning(request, "You are not marked as attending this event. Please RSVP first.")
        return redirect("club_member:event_detail", event_id=event.id)

    if request.method == "POST":
        if not attendance.checked_in:
            attendance.checked_in = True
            attendance.checked_in_at = timezone.now()
            attendance.save()
            django_messages.success(request, "You have successfully checked in!")
        else:
            django_messages.info(request, "You have already checked in.")
        return redirect("club_member:event_detail", event_id=event.id)

    return render(request, "club_member/qr_attendance_confirmation.html", {
        "event": event,
        "attendance_record": attendance,
    })

@login_required
def mark_attendance(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    attendance, created = EventAttendance.objects.update_or_create(
        user=request.user,
        event=event,
        defaults={'is_attending': True}
    )

    django_messages.success(request, f"You've been marked as attending: {event.title}")
    return redirect("club_member:event_detail", event_id=event.id)

