from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.timezone import make_aware
from django.core.exceptions import ValidationError
from faker import Faker
import random
from users.models import User, Membership
from clubs.models import Club, Event, Announcement, ClubDocument, Meeting, RescheduleRequest
from feedback.models import Feedback
from voting.models import Election, Position, Candidate, Vote
from analytics.models import ClubAnalytics
from club_member.models import MembershipTerminationRequest

class Command(BaseCommand):
    help = 'Seed the database with test data'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("\U0001F331 Seeding test data..."))

        fake = Faker()

        # Create Clubs
        clubs = []
        for _ in range(5):
            club = Club.objects.create(
                name=fake.unique.company(),
                description=fake.text(),
                quota=15
            )
            clubs.append(club)

        # Create Users
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

        # Assign memberships (1 leader + 2 members max)
        for i, user in enumerate(users):
            leader_club = clubs[i % len(clubs)]
            try:
                Membership.objects.create(user=user, club=leader_club, membership_type="leader")
            except ValidationError as e:
                self.stdout.write(self.style.WARNING(f"Skipping leader membership for {user.email}: {e}"))

            # Try assigning up to 2 member clubs, avoiding duplicates
            member_clubs = random.sample([c for c in clubs if c != leader_club], 4)
            member_count = 0
            for club in member_clubs:
                if member_count >= 2:
                    break
                try:
                    Membership.objects.create(user=user, club=club, membership_type="member")
                    member_count += 1
                except ValidationError as e:
                    self.stdout.write(self.style.WARNING(f"Skipping member membership for {user.email} in {club.name}: {e}"))

        # Create Events
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

        # Create Feedback
        for club in clubs:
            for _ in range(5):
                category = random.choice(["complaint", "suggestion"])
                submitted_by = random.choice(users) if category == "suggestion" else None
                Feedback.objects.create(
                    club=club,
                    submitted_by=submitted_by,
                    content=fake.paragraph(),
                    category=category
                )

        # Create Announcements
        for club in clubs:
            for _ in range(5):
                Announcement.objects.create(
                    club=club,
                    title=fake.bs(),
                    content=fake.text(),
                    visible=True
                )

        # Create Club Documents
        for club in clubs:
            for _ in range(4):
                ClubDocument.objects.create(
                    club=club,
                    title=fake.catch_phrase(),
                    file="club_documents/sample.pdf"
                )

        # Create ClubAnalytics, Meetings, Reschedule Requests, and Termination Requests
        for club in clubs:
            # Analytics
            analytics, _ = ClubAnalytics.objects.get_or_create(club=club)
            analytics.update_stats()

            # Meetings
            for _ in range(2):
                Meeting.objects.create(
                    club=club,
                    date_time=make_aware(fake.future_datetime(end_date="+30d")),
                    agenda=fake.paragraph(nb_sentences=3)
                )

            # Reschedule Request
            event = club.events.first()
            leader = club.get_leader()
            if event and leader:
                RescheduleRequest.objects.get_or_create(
                    event=event,
                    club_leader=leader.user,
                    status=random.choice(["pending", "approved"])
                )

            # Membership Termination Request
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

        # Create Voting Data
        election = Election.objects.create(
            name="Fall Election",
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=7),
            is_active=True
        )

        positions = ["President", "Vice-President", "Secretary"]
        for pos in positions:
            position = Position.objects.create(name=pos, election=election)
            candidates = random.sample(users, 2)
            for user in candidates:
                Candidate.objects.create(
                    election=election,
                    position=position,
                    user=user,
                    approved=True
                )

        self.stdout.write(self.style.SUCCESS("\u2705 Dummy data seeded successfully!"))
