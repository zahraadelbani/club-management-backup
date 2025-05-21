from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from voting.models import Election, Position, Candidate, Vote
from users.models import Membership
from clubs.models import Club
from faker import Faker
import random

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = "Simulates a full election lifecycle on a large scale with fast-forwarded timing."

    def handle(self, *args, **kwargs):
        # === 1. Setup ===
        club = Club.objects.create(name="Techno Club", description="Tech-focused club.", quota=200)
        self.stdout.write(self.style.SUCCESS(f"Created club: {club.name}"))

        # === 2. Create Users ===
        users = []
        for _ in range(100):
            user = User.objects.create_user(
                email=fake.unique.email(),
                name=fake.name(),
                password="testpass123",
                student_id=fake.unique.random_number(digits=8, fix_len=True),
                role="club_member"
            )
            Membership.objects.create(user=user, club=club, membership_type="member")
            users.append(user)
        self.stdout.write(self.style.SUCCESS(f"Created {len(users)} users with club membership"))

        # === 3. Create Election with short nomination/voting window ===
        now = timezone.now()
        election = Election.objects.create(
            name="Techno Club Election Stress Test",
            nomination_start=now,
            nomination_end=now + timezone.timedelta(minutes=5),
            start_date=now + timezone.timedelta(minutes=6),
            end_date=now + timezone.timedelta(minutes=10),
            is_active=True
        )
        self.stdout.write(self.style.SUCCESS(f"Election '{election.name}' created."))

        # === 4. Create Positions ===
        position_titles = ["President", "Vice President", "Secretary", "Treasurer", "Organizer"]
        positions = []
        for title in position_titles:
            pos = Position.objects.create(name=title, election=election, club=club)
            positions.append(pos)
        self.stdout.write(self.style.SUCCESS("Created election positions."))

        # === 5. Self-Nominations ===
        nominations = []
        for pos in positions:
            selected_users = random.sample(users, 10)
            for user in selected_users:
                if not Candidate.objects.filter(user=user, position=pos, election=election).exists():
                    candidate = Candidate.objects.create(
                        user=user,
                        position=pos,
                        club=club,
                        election=election,
                        manifesto=fake.sentence(),
                        self_nominated=True,
                        approved=True  # Assume ACA approves instantly for testing
                    )
                    nominations.append(candidate)
        self.stdout.write(self.style.SUCCESS(f"{len(nominations)} candidates self-nominated and approved."))

        # === 6. Fast-forward time to voting start ===
        election.start_date = timezone.now() - timezone.timedelta(minutes=1)
        election.save()

        # === 7. Voting Phase ===
        vote_count = 0
        for voter in users:
            for pos in positions:
                candidates = Candidate.objects.filter(position=pos, election=election, approved=True)
                if candidates.exists():
                    chosen = random.choice(list(candidates))
                    if not Vote.objects.filter(voter=voter, position=pos, election=election).exists():
                        Vote.objects.create(
                            voter=voter,
                            position=pos,
                            candidate=chosen,
                            election=election
                        )
                        chosen.votes += 1
                        chosen.save()
                        vote_count += 1
        self.stdout.write(self.style.SUCCESS(f"Voting complete. {vote_count} votes cast across {len(positions)} positions."))

        # === 8. Verify Results ===
        election.end_date = timezone.now() - timezone.timedelta(seconds=10)
        election.results_verified = True
        election.save()

        # === 9. Promote Winners ===
        for pos in positions:
            winner = Candidate.objects.filter(position=pos, election=election, approved=True).order_by('-votes').first()
            if winner:
                Membership.objects.update_or_create(
                    user=winner.user,
                    club=club,
                    defaults={"membership_type": "leader"}
                )
                self.stdout.write(self.style.SUCCESS(f"{winner.user.name} is now the {pos.name} (Leader)"))

        self.stdout.write(self.style.SUCCESS("\n✅ Large-scale election simulation completed successfully."))