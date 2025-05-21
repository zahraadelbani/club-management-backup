from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext as _
from .models import Poll, Choice, PollVote
from .forms import PollForm, ChoiceForm, ChoiceCountForm
from users.models import Membership


@login_required
def poll_list(request):
    memberships = Membership.objects.filter(user=request.user, membership_type__in=["leader", "member"])
    clubs = [m.club for m in memberships]
    polls = Poll.objects.filter(club__in=clubs, is_active=True).order_by("-created_at")
    return render(request, 'polls/poll_list.html', {'polls': polls})


@login_required
def select_num_choices(request):
    if request.method == "POST":
        form = ChoiceCountForm(request.POST)
        if form.is_valid():
            num_choices = int(form.cleaned_data['num_choices'])
            return redirect('polls:create_poll', num_choices=num_choices)
    else:
        form = ChoiceCountForm()
    return render(request, 'polls/select_num_choices.html', {'form': form})


@login_required
def create_poll(request, num_choices):
    membership = Membership.objects.filter(user=request.user, membership_type='leader').first()
    if not membership:
        messages.error(request, _("Only club leaders can create polls."))
        return redirect("polls:poll_list")

    if request.method == "POST":
        poll_form = PollForm(request.POST)
        choice_forms = [ChoiceForm(request.POST, prefix=str(i)) for i in range(num_choices)]
        if poll_form.is_valid() and all(cf.is_valid() for cf in choice_forms):
            poll = poll_form.save(commit=False)
            poll.club = membership.club
            poll.created_by = request.user
            poll.save()
            for choice_form in choice_forms:
                choice = choice_form.save(commit=False)
                choice.poll = poll
                choice.save()
            messages.success(request, _("Poll and choices created successfully."))
            return redirect('polls:poll_list')
    else:
        poll_form = PollForm()
        choice_forms = [ChoiceForm(prefix=str(i)) for i in range(num_choices)]

    return render(request, 'polls/create_poll.html', {
        'poll_form': poll_form,
        'choice_forms': choice_forms,
        'num_choices': num_choices
    })


@login_required
def Pollvote(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    is_member = Membership.objects.filter(user=request.user, club=poll.club, membership_type__in=["leader", "member"]).exists()
    if not is_member:
        messages.error(request, _("You are not authorized to vote in this poll."))
        return redirect("polls:poll_list")

    if PollVote.objects.filter(user=request.user, poll=poll).exists():
        messages.warning(request, _("You have already voted on this poll."))
        return redirect("polls:poll_results", poll_id=poll.id)

    if request.method == "POST":
        choice_id = request.POST.get("choice")
        choice = get_object_or_404(Choice, id=choice_id, poll=poll)
        PollVote.objects.create(user=request.user, poll=poll, choice=choice)
        choice.vote_count += 1
        choice.save()
        messages.success(request, _("Your vote has been submitted."))
        return redirect('polls:poll_results', poll_id=poll.id)

    return render(request, 'polls/vote.html', {'poll': poll})


@login_required
def poll_results(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    is_member = Membership.objects.filter(user=request.user, club=poll.club, membership_type__in=["leader", "member"]).exists()
    if not is_member:
        messages.error(request, _("You are not authorized to view this poll."))
        return redirect("polls:poll_list")
    return render(request, 'polls/poll_results.html', {'poll': poll})


@login_required
def update_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id, created_by=request.user)
    choices = poll.choices.all()

    if request.method == "POST":
        poll_form = PollForm(request.POST, instance=poll)
        choice_forms = [ChoiceForm(request.POST, prefix=str(choice.id), instance=choice) for choice in choices]
        new_choice_form = ChoiceForm(request.POST, prefix="new")

        if poll_form.is_valid() and all(cf.is_valid() for cf in choice_forms) and new_choice_form.is_valid():
            poll_form.save()
            for choice_form in choice_forms:
                choice_form.save()

            # Add a new choice if provided
            new_choice = new_choice_form.save(commit=False)
            if new_choice.text.strip():
                new_choice.poll = poll
                new_choice.save()

            messages.success(request, _("Poll updated successfully."))
            return redirect('polls:poll_list')

    else:
        poll_form = PollForm(instance=poll)
        choice_forms = [ChoiceForm(prefix=str(choice.id), instance=choice) for choice in choices]
        new_choice_form = ChoiceForm(prefix="new")

    return render(request, 'polls/update_poll.html', {
        'poll_form': poll_form,
        'choice_forms': choice_forms,
        'new_choice_form': new_choice_form,
        'poll': poll
    })


@login_required
def view_poll(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    is_member = Membership.objects.filter(user=request.user, club=poll.club, membership_type__in=["leader", "member"]).exists()
    if not is_member:
        messages.error(request, _("You are not authorized to view this poll."))
        return redirect("polls:poll_list")

    has_voted = PollVote.objects.filter(user=request.user, poll=poll).exists()
    return render(request, 'polls/view_poll.html', {
        'poll': poll,
        'has_voted': has_voted
    })
