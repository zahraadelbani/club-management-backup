from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Election, Position
from clubs.models import Club
from users.models import Membership

@receiver(post_save, sender=Election)
def reset_leaders_and_create_positions(sender, instance, created, **kwargs):
    if created:
        # Uncomment below to reset all leaders to 'member' when a new election is created
        # Membership.objects.filter(membership_type="leader").update(membership_type="member")

        # Auto-create 'President' position for each club
        all_clubs = Club.objects.all()
        for club in all_clubs:
            Position.objects.create(
                name="President",
                election=instance,
                club=club
            )
