from users.models import Membership

def is_leader(user):
    return user.role == "club_leader" or Membership.objects.filter(user=user, membership_type="leader").exists()

def is_aca(user):
    return user.role == "activity_center_admin"

def can_initiate_direct_chat(user_a, user_b):
    if user_a == user_b:
        return False

    # ✅ ACA ↔ Club Leader logic (by role or membership)
    if (is_aca(user_a) and is_leader(user_b)) or (is_aca(user_b) and is_leader(user_a)):
        return True

    # ✅ Same club (Leader ↔ Member, Member ↔ Member, etc.)
    clubs_a = set(Membership.objects.filter(user=user_a).values_list("club_id", flat=True))
    clubs_b = set(Membership.objects.filter(user=user_b).values_list("club_id", flat=True))
    return bool(clubs_a & clubs_b)
