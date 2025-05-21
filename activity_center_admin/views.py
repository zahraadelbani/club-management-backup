from django.http import HttpResponseForbidden, HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView
from django.utils.dateparse import parse_datetime
from django.core.mail import send_mail
from django.conf import settings
from activity_center_admin.forms import AnnouncementForm, ElectionForm
from clubs.forms import ClubForm, EventForm
from clubs.models import Club, Meeting, Event, Announcement
from notifications.utils import create_notification
from users.models import Membership, User
from voting.models import Candidate, Election
from django.utils.translation import gettext as _
from django.utils.timezone import now as timezone_now
from django.contrib.auth.decorators import login_required, user_passes_test
from voting.models import Election
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


# --- Helpers ---
def is_aca(user):
    return user.is_authenticated and user.get_role() == "activity_center_admin"

# --- Dashboard ---
@login_required
@user_passes_test(is_aca)
def activity_admin_dashboard(request):
    context = {
        'clubs': Club.objects.all(),
        'pending_events': Event.objects.filter(approval_status='pending', event_date__gte=timezone.now()).order_by('event_date'),
        'announcements': Announcement.objects.filter(visible=True).order_by('-created_at'),

    }
    return render(request, "activity_center_admin/dashboard.html", context)

# --- Clubs CRUD ---
class ClubListView(ListView):
    model = Club
    template_name = 'activity_center_admin/club_list.html'
    context_object_name = 'clubs'
    paginate_by = 6

class ClubCreateView(CreateView):
    model = Club
    form_class = ClubForm  # Use the custom form with image fields
    template_name = 'activity_center_admin/club_form.html'
    success_url = reverse_lazy('activity_center_admin:club_list')

    def form_valid(self, form):
        messages.success(self.request, _("Club created successfully."))
        return super().form_valid(form)

class ClubUpdateView(UpdateView):
    model = Club
    form_class = ClubForm
    form_class = ClubForm
    template_name = 'activity_center_admin/club_form.html'
    success_url = reverse_lazy('activity_center_admin:club_list')

    def form_valid(self, form):
        messages.success(self.request, _("Club updated successfully."))
        return super().form_valid(form)

class ClubDeleteView(DeleteView):
    model = Club
    success_url = reverse_lazy('activity_center_admin:club_list')

    def get(self, request, *args, **kwargs):
        # Prevent GET requests from deleting
        return HttpResponseRedirect(self.success_url)

    def post(self, request, *args, **kwargs):
        messages.success(request, _("Club deleted successfully."))
        return super().post(request, *args, **kwargs)

class EventCreateView(CreateView):
    model = Event
    form_class = EventForm
    template_name = 'activity_center_admin/event_form.html'
    success_url = reverse_lazy('activity_center_admin:event_list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.approval_status = 'approved'
        form.instance.rescheduled = False
        form.instance.club = None  # ✅ Force null club for ACA events
        form.save()
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": True})
        
        messages.success(self.request, _("Event created and published."))
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            return JsonResponse({"success": False, "errors": form.errors}, status=400)
        return render(self.request, self.template_name, {
            "form": form,
            "google_api_key": settings.GOOGLE_MAPS_API_KEY,  # ✅ Fix added here
        })

class EventUpdateView(UpdateView):
    model = Event
    form_class = EventForm
    template_name = 'activity_center_admin/event_form.html'
    success_url = reverse_lazy('activity_center_admin:aca_all_events')

    def dispatch(self, request, *args, **kwargs):
        event = self.get_object()
        user_role = request.user.get_role()

        if user_role == "activity_center_admin":
            return super().dispatch(request, *args, **kwargs)

        elif user_role == "club_leader":
            if event.club and Membership.objects.filter(
                club=event.club,
                user=request.user,
                membership_type="leader"
            ).exists():
                return super().dispatch(request, *args, **kwargs)
            else:
                return HttpResponseForbidden("You are not authorized to edit this event.")

        return HttpResponseForbidden("Unauthorized")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["google_api_key"] = settings.GOOGLE_MAPS_API_KEY
        context["event"] = self.object
        return context

    def form_valid(self, form):
        event = form.instance  # safer reference

        if event.created_by and event.created_by.get_role() == "activity_center_admin":
            event.approval_status = "approved"
            messages.success(self.request, _("ACA event updated successfully."))
        else:
            event.approval_status = "pending"
            messages.success(self.request, _("Event updated. Awaiting re-approval."))

        return super().form_valid(form)

class EventDeleteView(DeleteView):
    model = Event
    template_name = 'activity_center_admin/event_confirm_delete.html'
    success_url = reverse_lazy('activity_center_admin:aca_all_events')

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, _("Event deleted successfully."))
        return super().delete(request, *args, **kwargs)

@login_required
@user_passes_test(is_aca)
def aca_calendar_view(request):
    def paginate(queryset, prefix):
        page = request.GET.get(prefix + '_page')
        paginator = Paginator(queryset, 6)  # adjust per-page count
        return paginator.get_page(page)

    pending = paginate(Event.objects.filter(approval_status="pending").order_by("event_date"), 'pending')
    approved = paginate(Event.objects.filter(approval_status="approved").order_by("event_date"), 'approved')
    declined = paginate(Event.objects.filter(approval_status="rejected").order_by("event_date"), 'declined')

    upcoming_events = Event.objects.filter(event_date__gte=timezone.now()).order_by("event_date")[:4]

    return render(request, "activity_center_admin/event_list.html", {
        "pending_events": pending,
        "approved_events": approved,
        "declined_events": declined,
        "events": upcoming_events,
        "form": EventForm(),
        "google_api_key": settings.GOOGLE_MAPS_API_KEY,
    })


# --- View: ACA Upcoming Events List ---
@login_required
@user_passes_test(is_aca)
def aca_all_events(request):
    events = Event.objects.all().order_by("event_date")  # include all events
    paginator = Paginator(events, 10)  # Show 10 events per page

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "activity_center_admin/aca_all_events.html", {
        "events": page_obj,  # send paginated events
        "page_obj": page_obj,
        "google_api_key": settings.GOOGLE_MAPS_API_KEY,
        "form": EventForm(),
    })

@login_required
def get_all_approved_events(request):
    events = Event.objects.filter(approval_status="approved")
    data = []
    for e in events:
        data.append({
            "title": e.title,
            "start": e.event_date.isoformat(),
            "approval_status": e.approval_status,
            "club_name": e.club.name if e.club else None,  # ✅ FIXED
            "rescheduled": e.rescheduled,
            "type": "meeting" if "meeting" in e.title.lower() else "event"
        })
    return JsonResponse(data, safe=False)

@login_required
@user_passes_test(is_aca)
def get_event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    return JsonResponse({
        "title": event.title,
        "transportation_request": event.transportation_request,
        "total_cost": str(event.total_cost) if event.total_cost else None,
        "needs": event.needs,
        "location_name": event.location_name,
        "latitude": event.latitude,     # ✅ ADD THIS
        "longitude": event.longitude,   # ✅ AND THIS
        "image": event.image.url if event.image else None,


    })


@login_required
@user_passes_test(is_aca)
def event_approve(request, activity_id):
    activity = get_object_or_404(Event, id=activity_id)
    activity.approval_status = 'approved'
    activity.save()

    # Get all members and leaders of the club
    memberships = Membership.objects.filter(club=activity.club).select_related('user')
    
    for membership in memberships:
        # Set different URLs based on user role
        if membership.membership_type == "leader":
            notification_url = reverse("club_leader:calendar")
        else:
            notification_url = reverse("club_member:event_calendar")
            
        create_notification(
            user_id=membership.user_id,
            title="New Event Approved",
            message=f"The event '{activity.title}' has been approved in {activity.club.name}.",
            url=notification_url
        )

    messages.success(request, _("Event approved and members notified."))
    return redirect('activity_center_admin:event_list')

@login_required
@user_passes_test(is_aca)
def event_reject(request, activity_id):
    activity = get_object_or_404(Event, id=activity_id)
    activity.approval_status = 'rejected'
    activity.save()

    # Notify only club leaders about the rejection
    leaders = Membership.objects.filter(club=activity.club, membership_type="leader").select_related("user")
    calendar_url = reverse("club_leader:calendar")

    for leader in leaders:
        create_notification(
            user=leader.user,
            title=" Event Rejected",
            message=f"The event '{activity.title}' in {activity.club.name} has been rejected by the ACA.",
            url=calendar_url
        )

    messages.success(request, _("Event rejected and leaders notified."))
    return redirect('activity_center_admin:event_list')

@login_required
@user_passes_test(is_aca)
def schedule_meeting(request, activity_id):
    activity = get_object_or_404(Event, id=activity_id)

    if request.method == 'POST':
        date_time_str = request.POST.get('date_time')
        agenda = request.POST.get('agenda')

        date_time = parse_datetime(date_time_str)
        if not date_time:
            messages.error(request, _("Invalid date and time format."))
            return render(request, 'activity_center_admin/schedule_meeting_form.html', {'activity': activity})

        Meeting.objects.create(club=activity.club, date_time=date_time, agenda=agenda)
        activity.rescheduled = True
        activity.save()

        # Notify only leaders
        leaders = Membership.objects.filter(club=activity.club, membership_type="leader").select_related("user")
        calendar_url = reverse("club_leader:calendar")

        for leader in leaders:
            create_notification(
                user=leader.user,
                title="Meeting Scheduled",
                message=f"A meeting has been scheduled to review the event: '{activity.title}'.",
                url=calendar_url
            )

        messages.success(request, _("Meeting scheduled and leader notified."))
        return redirect('activity_center_admin:event_list')

    return render(request, 'activity_center_admin/schedule_meeting_form.html', {'activity': activity})



# --- Nomination Management ---
@login_required
@user_passes_test(is_aca)
def manage_nominations(request):
    pending_candidates = Candidate.objects.filter(self_nominated=True, approved=False)
    return render(request, "activity_center_admin/manage_nominations.html", {
        "pending_candidates": pending_candidates,
    })

@login_required
@user_passes_test(is_aca)
def approve_nomination(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id, self_nominated=True)
    candidate.approved = True
    candidate.save()

    # Notify the user
    create_notification(
        user=candidate.user,
        title="Nomination Approved",
        message=f"Your self-nomination for {candidate.position.name} has been approved.",
        url=reverse("club_member:dashboard"),
    )

    messages.success(request, _("Approved nomination for %(name)s.") % {"name": candidate.user.name})
    return redirect("activity_center_admin:manage_nominations")

@login_required
@user_passes_test(is_aca)
def reject_nomination(request, candidate_id):
    candidate = get_object_or_404(Candidate, id=candidate_id, self_nominated=True)

    # Save reference to user and position before deleting
    user = candidate.user
    position_name = candidate.position.name
    candidate.delete()

    # Notify the user
    create_notification(
        user=user,
        title="Nomination Rejected",
        message=f"Your self-nomination for {position_name} has been rejected.",
        url=reverse("club_member:dashboard"), 
    )

    messages.warning(request, _("Rejected nomination for %(name)s.") % {"name": user.name})
    return redirect("activity_center_admin:manage_nominations")

@login_required
@user_passes_test(is_aca)
def create_election(request):
    if request.method == "POST":
        form = ElectionForm(request.POST)
        if form.is_valid():
            election = form.save()

            # Notify users if the election is already active
            if election.is_active:
                memberships = Membership.objects.filter(
                    club__in=election.positions.values_list("club", flat=True).distinct(),
                    membership_type="member"
                ).select_related("user", "club")

                notified_users = set()
                for membership in memberships:
                    if membership.user_id not in notified_users:
                        create_notification(
                        user=membership.user,
                        title="Election Now Live",
                        message=f"The election '{election.name}' is now open for voting.",
                        url=reverse("voting:elections"),
                    )
                        notified_users.add(membership.user_id)

            messages.success(request, _("New election created!"))
            return redirect("activity_center_admin:manage_elections")
    else:
        form = ElectionForm()
    return render(request, "activity_center_admin/create_election.html", {"form": form})

@login_required
@user_passes_test(is_aca)
def edit_election(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    if request.method == "POST":
        form = ElectionForm(request.POST, instance=election)
        if form.is_valid():
            form.save()
            messages.success(request, _("Election updated!"))
            return redirect("activity_center_admin:manage_elections")
    else:
        form = ElectionForm(instance=election)

    return render(request, "activity_center_admin/edit_election.html", {
        "election": election,
        "form": form,
    })

@login_required
@user_passes_test(is_aca)
def delete_election(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    if request.method == "POST":
        election.delete()
        messages.success(request, _("Election deleted."))
        return redirect("activity_center_admin:manage_elections")
    return redirect("activity_center_admin:manage_elections")

@login_required
@user_passes_test(is_aca)
def manage_elections(request):
    elections = Election.objects.all().order_by("-start_date")
    current_time = timezone_now()

    for e in elections:
        if not e.nomination_start or not e.nomination_end or not e.start_date or not e.end_date:
            e.status = "Missing Dates"
            e.status_color = "bg-red-100 text-red-800"
            continue

        if current_time < e.nomination_start:
            e.status = "Upcoming"
            e.status_color = "bg-gray-200 text-gray-800"
        elif e.nomination_start <= current_time <= e.end_date:
            e.status = "Ongoing"
            e.status_color = "bg-yellow-100 text-yellow-800"
        else:
            e.status = "Ended"
            e.status_color = "bg-green-100 text-green-800"

    return render(request, "activity_center_admin/manage_elections.html", {
        "elections": elections,
        "now": current_time,  # ✅ pass this to template
    })

@login_required
@user_passes_test(is_aca)
def toggle_election_active(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    election.is_active = not election.is_active
    election.save()

    # Notify users only if the election was just activated
    if election.is_active:
        memberships = Membership.objects.filter(
            club__in=election.positions.values_list("club", flat=True).distinct(),
            membership_type="member"
        ).select_related("user", "club")

        notified_users = set()
        for membership in memberships:
            if membership.user_id not in notified_users:
                create_notification(
                user=membership.user,
                title="Election Activated",
                message=f"The election '{election.name}' is now live.",
                url=reverse("voting:elections"),
            )
                notified_users.add(membership.user_id)

    messages.success(
        request,
        _("Election '%(name)s' is now %(status)s.") % {
            "name": election.name,
            "status": _("active") if election.is_active else _("inactive")
        }
    )
    return redirect("activity_center_admin:manage_elections")

@login_required
@user_passes_test(is_aca)
def aca_announcements(request):
    filter_type = request.GET.get("type", "global")
    page = request.GET.get("page", 1)

    leader_ids = Membership.objects.filter(membership_type="leader").values_list("user_id", flat=True)

    base_query = Announcement.objects.filter(
        Q(created_by__in=leader_ids) |
        Q(created_by__role="activity_center_admin") |
        Q(created_by__isnull=True)
    )

    if filter_type == "club":
        announcements_qs = base_query.filter(club__isnull=False)
    elif filter_type == "all":
        announcements_qs = base_query
    else:  # global
        announcements_qs = base_query.filter(club__isnull=True)

    announcements_qs = announcements_qs.order_by("-created_at")
    paginator = Paginator(announcements_qs, 6)  # 6 per page
    announcements = paginator.get_page(page)

    return render(request, "activity_center_admin/announcement_list.html", {
        "announcements": announcements,
    })

@login_required
def toggle_announcement_visibility(request, pk):
    announcement = get_object_or_404(Announcement, pk=pk)
    announcement.visible = not announcement.visible
    announcement.save()

    if announcement.visible:
        # Notify all users except the current admin
        for user in User.objects.exclude(id=request.user.id):
            create_notification(
                    user=user,
                    title="New Global Announcement",
                    message=announcement.title,
                    url=reverse("club_member:member_announcements"),

                )

    return JsonResponse({'success': True, 'visible': announcement.visible})

@login_required
@user_passes_test(lambda u: u.get_role() == "activity_center_admin")
def aca_create_announcement(request):
    if request.method == "POST":
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.club = None  
            announcement.visible = True
            announcement.save()

            # Send notification to all users except ACA
            for user in User.objects.exclude(id=request.user.id):
                create_notification(
                    user=user,
                    title="New Global Announcement",
                    message=announcement.title,
                    url=reverse("club_member:member_announcements"),

                )

            messages.success(request, "Global announcement created and shared!")
            return redirect("activity_center_admin:announcement_list")
    else:
        form = AnnouncementForm()

    return render(request, "activity_center_admin/create_announcement.html", {"form": form})

def assign_club_leader(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    
    # Get search query
    search_query = request.GET.get('search', '')
    
    # Base queryset
    members = Membership.objects.filter(club=club, membership_type="member").select_related("user")
    
    # Apply search filter if query exists
    if search_query:
        members = members.filter(
            Q(user__name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(members, 10)  # 10 members per page
    try:
        members_page = paginator.page(page)
    except PageNotAnInteger:
        members_page = paginator.page(1)
    except EmptyPage:
        members_page = paginator.page(paginator.num_pages)

    if request.method == "POST":
        user_id = request.POST.get("user_id")
        selected_user = get_object_or_404(User, id=user_id)

        try:
            # Remove current leader(s)
            Membership.objects.filter(club=club, membership_type="leader").update(membership_type="member")

            # Promote selected user
            membership, created = Membership.objects.get_or_create(user=selected_user, club=club)
            membership.membership_type = "leader"
            membership.full_clean()
            membership.save()

            messages.success(request, _("Leader updated successfully."))
            return redirect("activity_center_admin:club_list")

        except ValidationError as e:
            messages.error(request, e.messages[0])

    context = {
        "club": club,
        "members": members_page,
        "search_query": search_query,
    }

    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, "activity_center_admin/assign_position.html", context)

    return render(request, "activity_center_admin/assign_position.html", context)

@login_required
@user_passes_test(is_aca)
def event_attendance_summary(request):
    club_id = request.GET.get("club")
    page_number = request.GET.get("page")

    clubs = Club.objects.all()
    events = Event.objects.filter(approval_status="approved").order_by("-event_date")

    if club_id:
        events = events.filter(club_id=club_id)

    summary = []
    for event in events:
        rsvp_count = event.attendances.filter(is_attending=True).count()
        if rsvp_count > 0:
            summary.append({
                "club": event.club.name if event.club else "EMU",
                "event": event.title,
                "date": event.event_date,
                "count": rsvp_count,
            })

    # Paginate the summary
    paginator = Paginator(summary, 5)  
    page_obj = paginator.get_page(page_number)

    return render(request, "activity_center_admin/event_attendance_summary.html", {
        "summary": page_obj,  # Send the paginated page
        "clubs": clubs,
        "selected_club_id": int(club_id) if club_id else None,
        "page_obj": page_obj,  # For pagination controls
    })