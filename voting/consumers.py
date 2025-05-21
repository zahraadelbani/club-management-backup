import json
from channels.generic.websocket import AsyncWebsocketConsumer
from voting.models import Election, Position, Candidate
from asgiref.sync import sync_to_async

class LiveResultsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.election_id = self.scope["url_route"]["kwargs"]["election_id"]
        self.room_group_name = f"election_{self.election_id}"

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        await self.send_results()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        pass  # No frontend messages expected

    async def send_results(self):
        data = await sync_to_async(self.get_results_data)()
        await self.send(text_data=json.dumps({
            "type": "live_results",
            "data": data
        }))

    def get_results_data(self):
        election = Election.objects.get(id=self.election_id)
        results = []
        for pos in Position.objects.filter(election=election):
            candidates = Candidate.objects.filter(position=pos, election=election, approved=True).order_by('-votes')
            results.append({
                "position_id": pos.id,  
                "position": pos.name,
                "club": pos.club.name if pos.club else "",
                "candidates": [
                    {"name": c.user.name, "votes": c.votes}
                    for c in candidates
                ]
            })
        return results

    async def broadcast_vote_update(self, event):
        await self.send_results()
