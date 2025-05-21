import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from clubs.models import Club
from users.models import User, Membership
from voting.models import Election, Position, Candidate, Vote
from cryptography.fernet import Fernet
from django.conf import settings

cipher_suite = Fernet(settings.SECRET_ENCRYPTION_KEY.encode())

class Command(BaseCommand):
    help = "Simulate full election workflow with voting and real-time results"

    def handle(self, *args, **kwargs):
        now = timezone.now()

        # 1. Create Election
        election = Election.objects.create(
            name="2025 Elections",
            start_date=now,
            end_date=now + timezone.timedelta(days=2),
            nomination_start=now - timezone.timedelta(days=1),
            nomination_end=now,
            is_active=True,
            results_verified=False
        )
        self.stdout.write(self.style.SUCCESS(f"Created Election: {election.name}"))

        # 2. Create President Positions (one per club)
        clubs = Club.objects.all()
        for club in clubs:
            Position.objects.create(
                name="President",
                election=election,
                club=club
            )

        self.stdout.write(self.style.SUCCESS(f"Created President positions for {clubs.count()} clubs"))

        # 3. Create Candidates (1–3 per club)
        for club in clubs:
            position = Position.objects.get(election=election, club=club)
            members = list(User.objects.filter(memberships__club=club, memberships__membership_type="member"))
            random.shuffle(members)
            for member in members[:random.randint(1, 3)]:
                Candidate.objects.create(
                    user=member,
                    election=election,
                    position=position,
                    club=club,
                    self_nominated=True,
                    approved=True
                )
            self.stdout.write(f"✓ Club '{club.name}' → {Candidate.objects.filter(position=position).count()} candidates")

        # 4. Simulate Voting
        for club in clubs:
            position = Position.objects.get(election=election, club=club)
            candidates = list(Candidate.objects.filter(position=position))
            voters = list(User.objects.filter(memberships__club=club, memberships__membership_type="member"))
            random.shuffle(voters)

            voted_users = set()
            for voter in voters[:random.randint(2, 5)]:
                if voter.id in voted_users:
                    continue
                candidate = random.choice(candidates)
                vote = Vote.objects.create(
                    election=election,
                    voter=voter,
                    position=position,
                    candidate=candidate,
                )
                voted_users.add(voter.id)
                decrypted_name = vote.get_decrypted_candidate()
                self.stdout.write(f"🗳️ {voter.name} voted for {decrypted_name} in '{club.name}'")

        # 5. Print Live WebSocket Payloads
        self.stdout.write("\n📡 Simulated WebSocket Payloads:\n")
        for position in Position.objects.filter(election=election):
            payload = {
                "position": position.name,
                "club": position.club.name if position.club else "",
                "candidates": [
                    {
                        "name": c.user.name,
                        "votes": c.votes
                    }
                    for c in Candidate.objects.filter(position=position).order_by("-votes")
                ]
            }
            self.stdout.write(str(payload))

        # 6. Verify and Assign Leaders
        election.results_verified = True
        election.save()

        for position in Position.objects.filter(election=election, name__iexact="President"):
            top_candidate = Candidate.objects.filter(position=position, approved=True).order_by("-votes").first()
            if top_candidate:
                Membership.objects.update_or_create(
                    user=top_candidate.user,
                    club=position.club,
                    defaults={"membership_type": "leader"}
                )
                self.stdout.write(self.style.SUCCESS(f"🏆 {top_candidate.user.name} assigned as Leader of {position.club.name}"))

        self.stdout.write(self.style.SUCCESS("\n✅ Election simulation complete."))
