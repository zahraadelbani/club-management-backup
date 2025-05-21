from datetime import timedelta, timezone
from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _
from activity_center_admin import models
from club_leader.decorators import get_leader_club
from club_leader.forms import AnnouncementForm, ClubDocumentForm, EventRequestForm
from notifications.utils import create_notification
from users.models import User, Membership
from club_member.models import MembershipTerminationRequest
from clubs.models import Announcement, ClubDocument, Event, RescheduleRequest, Club
from feedback.models import Feedback
from analytics.models import ClubAnalytics
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from clubs.models import Meeting
from django.db.models import Q


@login_required
def club_leader_dashboard(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized to access this dashboard."))

    documents = ClubDocument.objects.filter(club=club)
    membership_requests = Membership.objects.filter(club=club, membership_type="pending").order_by('-created_at')[:3]
    termination_requests = MembershipTerminationRequest.objects.filter(club=club, status="pending").order_by('-created_at')[:3]
    complaints_page = Feedback.objects.filter(club=club, category="complaint", status="pending").order_by('-created_at')[:3]
    suggestions_page = Feedback.objects.filter(club=club, category="suggestion", status="pending").order_by('-created_at')[:3]
    pending_events = Event.objects.filter(club=club, approval_status="pending").order_by('-event_date')[:3]
    announcements = Announcement.objects.filter(club=club)

    analytics, _ = ClubAnalytics.objects.get_or_create(club=club)
    analytics.update_stats()

    context = {
        "announcements": announcements,
        "complaints_page": complaints_page,
        "suggestions_page": suggestions_page,
        "analytics": analytics,
        "members_percentage": analytics.members_percentage(),
        "documents": documents,
        "club": club,
        "pending_events": pending_events,
        "membership_requests": membership_requests,
        "termination_requests": termination_requests,
    }
    return render(request, 'club_leader/dashboard.html', context)


@login_required
def review_feedback(request, feedback_id):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized to access this dashboard."))

    feedback = get_object_or_404(Feedback, id=feedback_id, club=club)
    feedback.status = "reviewed"
    feedback.save()
    messages.success(request, _("Feedback marked as reviewed."))

    # Send notification to the submitter (if it's a suggestion with a user)
    if feedback.submitted_by:
        create_notification(
            user=feedback.submitted_by,
            title=f" Your feedback to {club.name} was reviewed",
            message=feedback.content[:50] + "...",
            url=reverse("club_member:submit_feedback"),
        )

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("club_leader:dashboard")

@login_required
def club_feedback_list(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden("You're not authorized to access this page.")

    feedback_list = Feedback.objects.filter(club=club)

    # Filters
    category_filter = request.GET.get('category')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')

    if category_filter:
        feedback_list = feedback_list.filter(category=category_filter)
    if status_filter:
        feedback_list = feedback_list.filter(status=status_filter)
    if search_query:
        feedback_list = feedback_list.filter(content__icontains=search_query)

    feedback_list = feedback_list.order_by('-created_at')

    # Dynamic per_page selection
    per_page = request.GET.get('per_page', 5)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 5

    paginator = Paginator(feedback_list, per_page)
    page = request.GET.get('page')
    try:
        feedback_page = paginator.page(page)
    except PageNotAnInteger:
        feedback_page = paginator.page(1)
    except EmptyPage:
        feedback_page = paginator.page(paginator.num_pages)

    context = {
        "club": club,
        "feedback_page": feedback_page,
        "category_filter": category_filter,
        "status_filter": status_filter,
        "search_query": search_query,
        "per_page": per_page
    }
    return render(request, 'club_leader/feedback_list.html', context)

@login_required
def club_members(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    member_qs = Membership.objects.filter(club=club, membership_type="member").select_related("user").order_by("-created_at")
    termination_qs = MembershipTerminationRequest.objects.filter(club=club, status="pending").select_related("membership__user").order_by("-created_at")
    pending_qs = Membership.objects.filter(club=club, membership_type="pending").select_related("user").order_by("-created_at")

    def paginate(queryset, key):
        paginator = Paginator(queryset, 5)
        page = request.GET.get(f'{key}_page')
        return paginator.get_page(page)

    members = paginate(member_qs, "members")
    termination_requests = paginate(termination_qs, "termination")
    membership_requests = paginate(pending_qs, "pending")

    return render(request, "club_leader/members.html", {
        "members": members,
        "requests": termination_requests,
        "membership_requests": membership_requests,
        "club": club,
        "is_leader": True
    })


@login_required
def remove_member(request, member_id):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    member = get_object_or_404(Membership, id=member_id, club=club, membership_type="member")

    if request.method == "POST":
        member.delete()
        messages.success(request, _("Member successfully removed from the club."))
        return redirect("club_leader:club_members")

    raise PermissionDenied  # This ensures only POST requests are allowed

@login_required
def update_membership_status(request, membership_id, action):
    if request.method != 'POST':
        raise PermissionDenied

    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    membership_request = get_object_or_404(Membership, id=membership_id, club=club, membership_type="pending")
    
    if action == "approve":
        membership_request.membership_type = "member"
        membership_request.save()
        messages.success(request, _("Member request has been approved successfully."))
    else:  # reject
        membership_request.delete()
        messages.success(request, _("Member request has been rejected."))

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("club_leader:dashboard")

@login_required
def approve_termination_request(request, request_id):
    if request.method != 'POST':
        raise PermissionDenied

    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    request_obj = get_object_or_404(MembershipTerminationRequest, id=request_id, club=club)
    member = request_obj.membership
    user = member.user

    request_obj.status = "approved"
    request_obj.reviewed_at = timezone.now()
    request_obj.save()
    member.delete()

    # Determine if user is still a member of any other club
    still_member = Membership.objects.filter(
        user=user,
        membership_type="member"
    ).exists()

    redirect_url = reverse("club_member:dashboard") if still_member else reverse("users:udashboard")

    # Notify user
    create_notification(
        user=user,
        title=f" You’ve been removed from {club.name}",
        message="Your membership termination request has been approved.",
        url=redirect_url,
    )

    messages.success(request, _("Membership termination request has been approved. The member has been removed from the club."))

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("club_leader:dashboard")

@login_required
def reject_termination_request(request, request_id):
    if request.method != 'POST':
        raise PermissionDenied

    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    request_obj = get_object_or_404(MembershipTerminationRequest, id=request_id, club=club)
    user = request_obj.membership.user

    request_obj.status = "rejected"
    request_obj.reviewed_at = timezone.now()
    request_obj.save()

    # Notify user of rejection
    create_notification(
        user=user,
        title=f" Termination Rejected by {club.name}",
        message="Your request to leave the club was rejected by the club leader.",
        url=reverse("club_member:dashboard"),
    )

    messages.success(request, _("Membership termination request has been rejected."))

    next_url = request.POST.get("next")
    if next_url:
        return redirect(next_url)
    return redirect("club_leader:dashboard")

@login_required
def club_analytics(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    analytics, created = ClubAnalytics.objects.get_or_create(club=club)
    analytics.update_stats()
    return render(request, "club_leader/analytics.html", {"analytics": analytics, "club": club})

@login_required
def submit_event_request(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    if request.method == 'POST':
        form = EventRequestForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.club = club
            event.created_by = request.user
            event.approval_status = 'pending'
            event.save()

            # ✅ Notify all ACAs
            for aca in User.objects.filter(role="activity_center_admin"):
                create_notification(
                    user=aca,
                    title="New Event Submitted",
                    message=f"A new event '{event.title}' has been submitted by {club.name}.",
                    url=reverse("activity_center_admin:event_list")
                )

            return redirect('club_leader:calendar')
    else:
        form = EventRequestForm()

    return render(request, 'club_leader/submit_event.html', {
        'form': form,
        'google_api_key': settings.GOOGLE_MAPS_API_KEY
    })


@login_required
def upload_document(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    if request.method == 'POST':
        form = ClubDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.club = club
            document.uploaded_by = request.user
            document.save()
            messages.success(request, _("Document uploaded successfully!"))
            return redirect('club_leader:list_documents')
    else:
        form = ClubDocumentForm()
    return render(request, 'club_leader/upload_document.html', {'form': form})

@login_required
def delete_document(request, pk):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    document = get_object_or_404(ClubDocument, pk=pk, club=club)
    document.delete()
    messages.success(request, _("Document deleted successfully!"))
    return redirect('club_leader:list_documents')

@login_required
def list_documents(request):
    user_club_ids = Membership.objects.filter(
        user=request.user,
        membership_type__in=["leader", "member"]
    ).values_list("club_id", flat=True)

    documents_qs = ClubDocument.objects.filter(club_id__in=user_club_ids).order_by("-uploaded_at")

    paginator = Paginator(documents_qs, 5) 
    page_number = request.GET.get("page")
    try:
        documents = paginator.page(page_number)
    except PageNotAnInteger:
        documents = paginator.page(1)
    except EmptyPage:
        documents = paginator.page(paginator.num_pages)

    return render(request, "club_leader/list_documents.html", {
        "documents": documents,
        "is_leader": Membership.objects.filter(user=request.user, membership_type="leader").exists()
    })

@login_required
def create_announcement(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.club = club
            announcement.created_by = request.user
            announcement.save()

            if announcement.visible:
                for user in club.get_members().exclude(id=request.user.id):
                    create_notification(
                        user=user,
                        title=f" New Announcement in {club.name}",
                        message=announcement.title,
                        url=reverse("club_member:member_announcements"),
                    )

            messages.success(request, _("Announcement created successfully!"))
            return redirect("club_leader:list_announcements")
    else:
        form = AnnouncementForm()
    return render(request, "club_leader/create_announcement.html", {"form": form})

@login_required
def list_announcements(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    announcements_list = Announcement.objects.filter(club=club).order_by("-created_at")

    # Pagination
    page = request.GET.get("page")
    paginator = Paginator(announcements_list, 6)
    try:
        announcements = paginator.page(page)
    except PageNotAnInteger:
        announcements = paginator.page(1)
    except EmptyPage:
        announcements = paginator.page(paginator.num_pages)

    context = {
        "announcements": announcements,
        "is_leader": True,
    }
    return render(request, "club_leader/list_announcements.html", context)

@login_required
def delete_announcement(request, pk):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    announcement = get_object_or_404(Announcement, pk=pk, club=club)
    announcement.delete()
    messages.success(request, _("Announcement deleted successfully!"))
    return redirect("club_leader:list_announcements")

@login_required
def edit_announcement(request, pk):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    announcement = get_object_or_404(Announcement, pk=pk, club=club)
    if request.method == "POST":
        form = AnnouncementForm(request.POST, instance=announcement)
        if form.is_valid():
            form.save()
            messages.success(request, _("Announcement updated successfully!"))
            return redirect("club_leader:list_announcements")
    else:
        form = AnnouncementForm(instance=announcement)
    return render(request, "club_leader/edit_announcement.html", {"form": form})

@login_required
def toggle_visibility(request, pk):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    announcement = get_object_or_404(Announcement, pk=pk, club=club)
    announcement.visible = not announcement.visible
    announcement.save()

    # Notify club members if it's now visible
    if announcement.visible:
        for user in club.get_members().exclude(id=request.user.id):
            create_notification(
                user=user,
                title=f"New Announcement in {club.name}",
                message=announcement.title,
                url=reverse("club_member:member_announcements"),
            )

    return JsonResponse({
        'success': True,
        'visible': announcement.visible,
    })

@login_required
def event_calendar(request):
    club_ids = Membership.objects.filter(
        user=request.user
    ).values_list("club_id", "membership_type")

    leader_club_ids = [club_id for club_id, role in club_ids if role == "leader"]
    member_club_ids = [club_id for club_id, role in club_ids if role == "member"]

    events = Event.objects.filter(
        Q(club__in=leader_club_ids) |  # Leader → see all events (any status)
        Q(club__in=member_club_ids, approval_status="approved") |  # Member → only approved
        Q(club__isnull=True, approval_status="approved")  # ACA → only approved
    ).filter(
        event_date__gte=timezone.now()
    ).order_by("event_date")[:4]

    meetings = Meeting.objects.filter(club__in=[cid for cid, _ in club_ids]).order_by("date_time")
    form = EventRequestForm()

    return render(request, 'club_leader/calendar.html', {
        'events': events,
        'meetings': meetings,
        'form': form,
        'club': get_leader_club(request.user),
        'google_api_key': settings.GOOGLE_MAPS_API_KEY
    })

@login_required
def get_events(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    cutoff_date = timezone.now() - timedelta(days=14)

    # Include: leader's own club (any status), ACA events (only approved), both within 14 days
    events = Event.objects.filter(
        event_date__gte=cutoff_date
    ).filter(
        Q(club=club) | Q(club__isnull=True, approval_status="approved")
    )

    meetings = Meeting.objects.filter(club=club)
    event_list = []

    for e in events:
        event_list.append({
            "title": f" {e.title}" if not e.rescheduled else f" {e.title} (Meeting Scheduled)",
            "start": e.event_date.isoformat(),
            "approval_status": e.approval_status,
            "rescheduled": e.rescheduled,
            "club_name": e.club.name if e.club else "EMU",
        })

    for m in meetings:
        leader = m.club.get_leader()
        event_list.append({
            "title": "Meeting",
            "start": m.date_time.isoformat(),
            "extendedProps": {
                "approval_status": "meeting",
                "type": "meeting",
                "description": m.agenda,
                "club_name": m.club.name,
                "leader_name": leader.user.name if leader else "N/A",
                "datetime": m.date_time.strftime("%B %d, %Y %I:%M %p"),
            }
        })

    return JsonResponse(event_list, safe=False)

@login_required
def edit_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    club = get_leader_club(request.user)

    if not club or event.club != club:
        return HttpResponseForbidden(_("You're not authorized to edit this event."))

    if request.method == "POST":
        form = EventRequestForm(request.POST, request.FILES, instance=event)

        if "transportation_request" not in request.POST:
            form.instance.transportation_request = False

        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully! Approval required."))
            return redirect(reverse("club_leader:edit_event", kwargs={"event_id": event.id}))
    else:
        form = EventRequestForm(instance=event)

    return render(request, "club_leader/edit_event.html", {"form": form, "event": event, "google_api_key": settings.GOOGLE_MAPS_API_KEY})

@login_required
def list_all_events(request):
    club = get_leader_club(request.user)
    if not club:
        return HttpResponseForbidden(_("You're not authorized."))

    cutoff_date = timezone.now() - timedelta(days=14)

    events_queryset = Event.objects.filter(
        Q(event_date__gte=cutoff_date),
        Q(club=club) | Q(club__isnull=True, approval_status="approved")
    ).order_by('event_date')

    paginator = Paginator(events_queryset, 5)  # 10 events per page
    page_number = request.GET.get('page')
    events_page = paginator.get_page(page_number)

    form = EventRequestForm()
    return render(request, 'club_leader/list_all_events.html', {
        'events': events_page,
        'form': form,
    })

@login_required
def faq_leader(request):
    if not Membership.objects.filter(user=request.user, membership_type='leader').exists():
        return HttpResponseForbidden("You are not authorized to view this page.")
    
    return render(request, 'Club_leader/faq_leader.html')

@login_required
def update_event_image(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    club = get_leader_club(request.user)

    if not club or event.club != club:
        return HttpResponseForbidden("You're not authorized.")

    if request.method == "POST" and request.FILES.get("image"):
        event.image = request.FILES["image"]
        event.save()
        messages.success(request, "Event image updated successfully!")

    return redirect("club_leader:edit_event", event_id=event_id)

def view_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return render(request, 'club_leader/view_event.html', {'event': event})