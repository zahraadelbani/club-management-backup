from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib import messages
 
from .models import Feedback
from clubs.models import Club
 
@login_required
def submit_feedback(request):
    user = request.user
 
    # Fetch user's clubs (leader or member)
    user_clubs = Club.objects.filter(
        memberships__user=user,
        memberships__membership_type__in=["member", "leader"]
    ).distinct()
 
    if request.method == "POST":
        club_id = request.POST.get("club_id")
        content = request.POST.get("content")
        category = request.POST.get("category")
 
        # Validate club membership
        club = get_object_or_404(user_clubs, id=club_id)
 
        if category not in ['complaint', 'suggestion']:
            messages.error(request, _("Invalid category selected."))
            # Show form again with pagination
            feedback_qs = Feedback.objects.filter(
                Q(submitted_by=user) | 
                Q(submitted_by=None, category="complaint", club__in=user_clubs)
            ).order_by('-created_at')
 
            paginator = Paginator(feedback_qs, 5)
            page = request.GET.get('page')
            try:
                feedback_list = paginator.page(page)
            except PageNotAnInteger:
                feedback_list = paginator.page(1)
            except EmptyPage:
                feedback_list = paginator.page(paginator.num_pages)
 
            return render(request, "club_member/submit_feedback.html", {
                "clubs": user_clubs,
                "feedback_list": feedback_list,
                "per_page": 5
            })
 
        Feedback.objects.create(
            club=club,
            submitted_by=None if category == "complaint" else user,
            content=content,
            category=category
        )
 
        if category == "complaint":
            messages.success(request, _("Your anonymous complaint has been submitted."))
        else:
            messages.success(request, _("Your suggestion has been submitted."))
 
        return redirect("club_member:submit_feedback")
 
    # GET Request: prepare feedback list
    feedback_qs = Feedback.objects.filter(
        Q(submitted_by=user) | 
        Q(submitted_by=None, category="complaint", club__in=user_clubs)
    ).order_by('-created_at')
 
    per_page = request.GET.get('per_page', 5)
    try:
        per_page = int(per_page)
    except ValueError:
        per_page = 5
 
    paginator = Paginator(feedback_qs, per_page)
    page = request.GET.get('page')
    try:
        feedback_list = paginator.page(page)
    except PageNotAnInteger:
        feedback_list = paginator.page(1)
    except EmptyPage:
        feedback_list = paginator.page(paginator.num_pages)
 
    return render(request, "club_member/submit_feedback.html", {
        "clubs": user_clubs,
        "feedback_list": feedback_list,
        "per_page": per_page
    })