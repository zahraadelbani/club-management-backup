from users.models import Membership

def get_leader_club(user):
    membership = Membership.objects.filter(user=user, membership_type="leader").first()
    if not membership:
        return None
    return membership.club
