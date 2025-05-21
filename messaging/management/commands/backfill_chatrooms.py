from django.core.management.base import BaseCommand
from clubs.models import Club
from messaging.models import ChatRoom

class Command(BaseCommand):
    help = "Create missing chat rooms for existing clubs"

    def handle(self, *args, **kwargs):
        count = 0
        for club in Club.objects.all():
            if not hasattr(club, "chat_room"):
                ChatRoom.objects.create(
                    club=club,
                    name=f"{club.name} Chat"
                )
                count += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Created {count} missing chat room(s)."))
