import json
import os
import time
import difflib
import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils.html import escape
from difflib import get_close_matches
from django.utils.translation import gettext_lazy as _

# Load FAQ data once
with open('chatbot/faq_data.json', 'r', encoding='utf-8') as f:
    FAQ_DATA = json.load(f)

OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "tinyllama"
OLLAMA_TIMEOUT = 30


def get_fuzzy_answer(user_message):
    if not isinstance(FAQ_DATA, dict):
        raise ValueError("FAQ_DATA must be a dictionary")
    questions = list(FAQ_DATA.keys())
    match = get_close_matches(user_message.lower(), questions, n=1, cutoff=0.6)
    if match:
        return FAQ_DATA[match[0]]
    return None

@csrf_exempt
@login_required
def chatbot_response(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request method."}, status=405)

    try:
        data = json.loads(request.body)
        prompt = data.get("message", "").strip()

        if not prompt:
            return JsonResponse({"response": _("Please type a message to start.")})

        # Get user info
        user = request.user
        user_name = escape(user.name)
        user_email = escape(user.email)
        user_role = user.get_role()

        # Handle hardcoded overrides
        normalized_prompt = prompt.lower()

        if normalized_prompt in ["who am i", "who am i?"]:
            short_identity = f"You're {user_name}, a {user_role.lower()}."
            return JsonResponse({"response": short_identity})

        elif normalized_prompt in ["what can you do", "what can you do?", "help", "how can you help me?"]:
            help_text = (
                "I can answer questions about clubs, events, meetings, announcements, and your profile. "
                "Try asking: 'What events are coming up?' or 'Who leads my club?'"
            )
            return JsonResponse({"response": help_text})

        elif normalized_prompt in ["tell me about my club", "what is my club", "my club info"]:
            from clubs.models import Membership  # Adjust import path to your project structure
            memberships = Membership.objects.filter(user=user, membership_type__in=["member", "leader"])

            if memberships.exists():
                clubs_info = ", ".join([m.club.name for m in memberships])
                club_msg = f"You're part of: {clubs_info}."
            else:
                club_msg = "You're not currently a member of any club."

            return JsonResponse({"response": club_msg})

        # Fuzzy match from FAQ
        fuzzy_answer = get_fuzzy_answer(prompt)
        if fuzzy_answer:
            time.sleep(1.2)
            return JsonResponse({"response": fuzzy_answer})

        # Prepare LLM fallback prompt
        system_prompt = (
            "You are ClubBot, a helpful assistant in a university club system.\n"
            "If the user asks 'who am I', respond using the user profile below.\n"
            "Answer every question in ONE short sentence. Be clear and concise.\n\n"
            f"User message: {prompt}\n"
            f"User Info: Name = {user_name}, Role = {user_role}, Email = {user_email}"
        )

        payload = {
            "model": OLLAMA_MODEL,
            "prompt": system_prompt,
            "stream": False
        }

        try:
            os.environ["NO_PROXY"] = "localhost,127.0.0.1"
            res = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
            res.raise_for_status()
            response_data = res.json()
            llm_response = response_data.get("response", _("Sorry, I didn't quite get that."))
        except (requests.RequestException, ValueError) as e:
            print(f"[❌] Ollama LLM error: {e}")
            llm_response = _("Sorry, I'm having trouble accessing deeper answers right now. Please try again later.")

        time.sleep(1.5)
        return JsonResponse({"response": llm_response})

    except Exception as e:
        print(f"[❌] Internal chatbot error: {e}")
        return JsonResponse({"response": _("Oops! Something went wrong. Please try again later.")}, status=500)
