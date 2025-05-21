from users.models import Membership
from voting.models import Election, Vote, Candidate
from clubs.models import Club  # assuming this is where Club is defined
from django.utils import timezone

def membership_roles(request):
    if not request.user.is_authenticated:
        return {}

    memberships = Membership.objects.filter(user=request.user)

    is_leader = memberships.filter(membership_type="leader").exists()
    is_member = memberships.filter(membership_type="member").exists()

    # Get leader's club (assumes one leader per club)
    leader_membership = memberships.filter(membership_type="leader").first()
    user_club = leader_membership.club if leader_membership else None

    # For voting
    voting_elections = []
    if is_member:
        active_elections = Election.objects.filter(
            is_active=True,
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now()
        )
        voting_elections = [
            e for e in active_elections
            if not Vote.objects.filter(election=e, voter=request.user).exists()
        ]

    election = Election.get_current_election()
    user_already_nominated = False
    if election and election.is_nomination_open():
        user_already_nominated = Candidate.objects.filter(user=request.user, election=election).exists()

    return {
        "is_leader": is_leader,
        "is_member": is_member,
        "user_club": user_club,
        "election_class": Election,
        "voting_elections": voting_elections,
        "election": election,
        "user_already_nominated": user_already_nominated,
    }
