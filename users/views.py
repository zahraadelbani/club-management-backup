from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from clubs.models import Announcement, Club
from .models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import ProfileUpdateForm
from users.models import Membership
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth.decorators import user_passes_test
from django.core.paginator import Paginator

@login_required
def user_dashboard(request):
    user = request.user

    if Membership.objects.filter(user=user, membership_type="member").exists():
        messages.info(request, _("You are now a club member!"))
        return render(request, "users/udashboard.html")

    applied_club_ids = Membership.objects.filter(user=user).values_list("club_id", flat=True)
    club_queryset = Club.objects.exclude(id__in=applied_club_ids)
    clubs = [club for club in club_queryset if club.get_member_count() < club.quota]

    # Apply pagination here
    paginator = Paginator(clubs, 4)  
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    pending_memberships = Membership.objects.filter(user=user, membership_type="pending").select_related("club")

    return render(request, "users/udashboard.html", {
        "clubs": page_obj,
        "page_obj": page_obj,
        "applied_clubs": applied_club_ids,
        "pending_memberships": pending_memberships
    })

@login_required
def announcements_view(request):
    announcements = Announcement.objects.filter(
        visible=True,
        club__isnull=True
    ).order_by("-created_at")

    paginator = Paginator(announcements, 2)  
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "users/announcements.html", {
        "announcements": page_obj,
        "page_obj": page_obj,
    })

@login_required
def apply_to_club(request, club_id):
    club = get_object_or_404(Club, id=club_id)

    if club.get_member_count() >= club.quota:
        messages.error(request, _("This club is full and cannot accept new members."))
        return redirect("users:udashboard")

    if Membership.objects.filter(user=request.user, club=club).exists():
        messages.info(request, _("You've already applied to this club."))
    else:
        try:
            Membership.objects.create(user=request.user, club=club, membership_type="pending")
            messages.success(request, _("Application to %(club)s sent!") % {"club": club.name})
        except ValidationError as e:
            messages.error(request, _(e.messages[0]))  

    return redirect("users:udashboard")

@login_required
def check_membership_status(request):
    accepted = Membership.objects.filter(user=request.user, membership_type="member").exists()
    return JsonResponse({"accepted": accepted})

@login_required
def cancel_application(request, club_id):
    membership = get_object_or_404(
        Membership,
        user=request.user,
        club__id=club_id,
        membership_type="pending"
    )
    membership.delete()
    messages.success(request, _("Your application to %(club)s has been withdrawn.") % {"club": membership.club.name})
    return redirect("users:udashboard")

# Navbar
@login_required
def navbar(request):
    return render(request, "navbar.html", {"user": request.user})

@login_required
def profile_view(request):
    user = request.user
    form = ProfileUpdateForm(instance=user)

    leader_memberships = Membership.objects.filter(user=user, membership_type='leader')
    member_memberships = Membership.objects.filter(user=user, membership_type='member')

    if request.method == "POST":
        if "profile_picture" in request.FILES:
            uploaded_file = request.FILES["profile_picture"]
            if user.profile_picture:
                user.profile_picture.delete(save=False)
            user.profile_picture = uploaded_file
            user.save()
            messages.success(request, _("Profile picture updated successfully!"))
            return redirect(request.path)

        elif "update_profile" in request.POST:
            form = ProfileUpdateForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, _("Profile updated successfully!"))
                return redirect(request.path)
            else:
                messages.error(request, _("Failed to update profile. Please check the form."))

    context = {
        "user": user,
        "form": form,
        "leader_memberships": leader_memberships,
        "member_memberships": member_memberships,
    }
    return render(request, "users/profile.html", context)


@login_required
@user_passes_test(lambda u: u.is_superuser)
def list_users(request):
    role_filter = request.GET.get('role')
    status_filter = request.GET.get('status')

    users = User.objects.all()

    if role_filter:
        users = users.filter(role=role_filter)

    if status_filter:
        users = users.filter(is_active=status_filter)

    paginator = Paginator(users, 10)  # Show 10 users per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    roles = User.ROLE_CHOICES
    statuses = User.STATUS_CHOICES

    return render(request, 'users/list_users.html', {
        'page_obj': page_obj,
        'users': page_obj.object_list,
        'roles': roles,
        'statuses': statuses,
        'selected_role': role_filter,
        'selected_status': status_filter,
    })


@login_required
def create_user(request):
    clubs = Club.objects.all()

    if request.method == 'POST':
        name = request.POST['name']
        email = request.POST['email']
        password = request.POST['password']
        role = request.POST['role']
        student_id = request.POST['student_id']
        club_id = request.POST.get('club_id')
        membership_type = request.POST.get('membership_type')

        try:
            user = User.objects.create_user(email=email, name=name, password=password, role=role, student_id=student_id)

            if club_id:
                club = Club.objects.get(id=club_id)
                Membership.objects.create(user=user, club=club, membership_type=membership_type)

            messages.success(request, _("User created successfully."))
            return redirect('users:list_users')

        except Exception as e:
            messages.error(request, _("An error occurred while creating the user: ") + str(e))

    return render(request, 'users/create_user.html', {'clubs': clubs})


@login_required
def update_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    memberships = Membership.objects.filter(user=user).select_related("club")

    if request.method == 'POST':
        user.name = request.POST['name']
        user.email = request.POST['email']
        user.student_id = request.POST['student_id']
        user.is_active = request.POST['status']
        user.role = request.POST['role']
        user.save()

        validation_error_occurred = False

        for membership in memberships:
            field_name = f"membership_type_{membership.id}"
            new_type = request.POST.get(field_name)
            if new_type and new_type != membership.membership_type:
                membership.membership_type = new_type
                try:
                    membership.save()
                except ValidationError as e:
                    messages.error(request, _("Error updating membership: ") + e.messages[0])
                    validation_error_occurred = True

        if validation_error_occurred:
            return render(request, 'users/update_user.html', {
                'user': user,
                'memberships': memberships,
            })

        messages.success(request, _("User and memberships updated successfully."))
        return redirect('users:list_users')

    return render(request, 'users/update_user.html', {
        'user': user,
        'memberships': memberships,
    })


@login_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, _("User deleted."))
    return redirect('users:list_users')
