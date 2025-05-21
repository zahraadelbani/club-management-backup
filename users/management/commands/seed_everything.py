from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import make_aware
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from faker import Faker
import random

from users.models import Membership
from clubs.models import Club, Event, Announcement, ClubDocument, Meeting, RescheduleRequest
from feedback.models import Feedback
from voting.models import Election, Position, Candidate, Vote
from analytics.models import ClubAnalytics
from club_member.models import MembershipTerminationRequest

User = get_user_model()
fake = Faker()

class Command(BaseCommand):
    help = 'Seeds all test data and simulates a full election cycle.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🌱 Seeding everything..."))

        # === 1. Seed General Clubs & Users ===
        clubs = []
        for _ in range(5):
            club = Club.objects.create(
                name=fake.unique.company(),
                description=fake.text(),
                quota=15
            )
            clubs.append(club)

        users = []
        for _ in range(10):
            user = User.objects.create_user(
                name=fake.name(),
                email=fake.unique.email(),
                password='testpass123',
                student_id=fake.random_number(digits=8, fix_len=True),
                role="club_member"
            )
            users.append(user)

        for i, user in enumerate(users):
            leader_club = clubs[i % len(clubs)]
            try:
                Membership.objects.create(user=user, club=leader_club, membership_type="leader")
            except ValidationError:
                pass
            for club in random.sample([c for c in clubs if c != leader_club], 2):
                try:
                    Membership.objects.create(user=user, club=club, membership_type="member")
                except ValidationError:
                    pass

        for club in clubs:
            for _ in range(3):
                Event.objects.create(
                    title=fake.catch_phrase(),
                    club=club,
                    event_date=make_aware(fake.future_datetime(end_date="+30d")),
                    participants=fake.name(),
                    needs=fake.sentence(),
                    total_cost=random.uniform(100, 1000),
                    transportation_request=random.choice([True, False]),
                    approval_status=random.choice(['pending', 'approved']),
                    created_by=random.choice(users)
                )

            for _ in range(5):
                category = random.choice(["complaint", "suggestion"])
                submitted_by = random.choice(users) if category == "suggestion" else None
                Feedback.objects.create(
                    club=club,
                    submitted_by=submitted_by,
                    content=fake.paragraph(),
                    category=category
                )

            for _ in range(5):
                Announcement.objects.create(
                    club=club,
                    title=fake.bs(),
                    content=fake.text(),
                    visible=True
                )

            for _ in range(4):
                ClubDocument.objects.create(
                    club=club,
                    title=fake.catch_phrase(),
                    file="club_documents/sample.pdf"
                )

            ClubAnalytics.objects.get_or_create(club=club)[0].update_stats()

            for _ in range(2):
                Meeting.objects.create(
                    club=club,
                    date_time=make_aware(fake.future_datetime(end_date="+30d")),
                    agenda=fake.paragraph(nb_sentences=3)
                )

            event = club.events.first()
            leader = club.get_leader()
            if event and leader:
                RescheduleRequest.objects.get_or_create(
                    event=event,
                    club_leader=leader.user,
                    status=random.choice(["pending", "approved"])
                )

            members = Membership.objects.filter(club=club, membership_type="member")
            if members.exists():
                member = random.choice(members)
                MembershipTerminationRequest.objects.create(
                    membership=member,
                    club=club,
                    status=random.choice(["pending", "approved", "rejected"]),
                    created_at=timezone.now(),
                    reviewed_at=timezone.now() if random.choice([True, False]) else None
                )

        # === 2. Full Election Lifecycle (Stress Test) ===
        techno_club = Club.objects.create(name="Techno Club", description="Tech-focused club.", quota=200)
        techno_users = []
        for _ in range(100):
            user = User.objects.create_user(
                email=fake.unique.email(),
                name=fake.name(),
                password="testpass123",
                student_id=fake.unique.random_number(digits=8, fix_len=True),
                role="club_member"
            )
            Membership.objects.create(user=user, club=techno_club, membership_type="member")
            techno_users.append(user)

        now = timezone.now()
        election = Election.objects.create(
            name="Techno Club Election Stress Test",
            nomination_start=now,
            nomination_end=now + timezone.timedelta(minutes=5),
            start_date=now + timezone.timedelta(minutes=6),
            end_date=now + timezone.timedelta(minutes=10),
            is_active=True
        )

        position_titles = ["President", "Vice President", "Secretary", "Treasurer", "Organizer"]
        positions = [Position.objects.create(name=title, election=election, club=techno_club) for title in position_titles]

        nominations = []
        for pos in positions:
            selected_users = random.sample(techno_users, 10)
            for user in selected_users:
                if not Candidate.objects.filter(user=user, position=pos, election=election).exists():
                    candidate = Candidate.objects.create(
                        user=user,
                        position=pos,
                        club=techno_club,
                        election=election,
                        manifesto=fake.sentence(),
                        self_nominated=True,
                        approved=True
                    )
                    nominations.append(candidate)

        election.start_date = timezone.now() - timezone.timedelta(minutes=1)
        election.save()

        vote_count = 0
        for voter in techno_users:
            for pos in positions:
                candidates = Candidate.objects.filter(position=pos, election=election, approved=True)
                if candidates.exists() and not Vote.objects.filter(voter=voter, position=pos, election=election).exists():
                    chosen = random.choice(list(candidates))
                    Vote.objects.create(
                        voter=voter,
                        position=pos,
                        candidate=chosen,
                        election=election
                    )
                    chosen.votes += 1
                    chosen.save()
                    vote_count += 1

        election.end_date = timezone.now() - timezone.timedelta(seconds=10)
        election.results_verified = True
        election.save()

        for pos in positions:
            winner = Candidate.objects.filter(position=pos, election=election, approved=True).order_by('-votes').first()
            if winner:
                Membership.objects.update_or_create(
                    user=winner.user,
                    club=techno_club,
                    defaults={"membership_type": "leader"}
                )

        self.stdout.write(self.style.SUCCESS("🎉 Everything seeded and simulated successfully."))
