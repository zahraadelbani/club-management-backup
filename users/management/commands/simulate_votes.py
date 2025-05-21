import random
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from voting.models import Election, Position, Candidate, Vote
from django.utils import timezone

User = get_user_model()

class Command(BaseCommand):
    help = "Simulates votes for a given election."

    def add_arguments(self, parser):
        parser.add_argument('election_id', type=int)
        parser.add_argument('--count', type=int, default=50)

    def handle(self, *args, **options):
        election_id = options['election_id']
        vote_count = options['count']

        try:
            election = Election.objects.get(id=election_id)
        except Election.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Election with ID {election_id} not found."))
            return

        positions = Position.objects.filter(election=election)
        members = User.objects.filter(role='club_member')

        if not positions.exists() or not members.exists():
            self.stdout.write(self.style.ERROR("No positions or members found."))
            return

        self.stdout.write(f"Simulating {vote_count} votes...")

        created = 0
        for _ in range(vote_count):
            voter = random.choice(members)
            position = random.choice(positions)
            candidates = Candidate.objects.filter(position=position, election=election, approved=True)

            if not candidates.exists():
                continue

            candidate = random.choice(candidates)

            # Skip if user already voted for this position
            if Vote.objects.filter(election=election, position=position, voter=voter).exists():
                continue

            Vote.objects.create(
                election=election,
                position=position,
                candidate=candidate,
                voter=voter,
                timestamp=timezone.now()
            )
            created += 1

        self.stdout.write(self.style.SUCCESS(f"{created} votes simulated."))
