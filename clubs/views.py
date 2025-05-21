from django.shortcuts import render, get_object_or_404
from .models import Club
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, EventAttendance
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import now
import json

def club_detail(request, club_id):
    club = get_object_or_404(Club, id=club_id)
    return render(request, "clubs/club_detail.html", {"club": club})

@csrf_exempt
def check_in_view(request):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            event_id = int(data.get("event_id"))

            event = Event.objects.get(id=event_id)
            attendance, _ = EventAttendance.objects.get_or_create(
                user=request.user,
                event=event,
                defaults={'is_attending': True}
            )
            attendance.is_attending = True
            attendance.checked_in = True
            attendance.checked_in_at = now()
            attendance.save()

            return JsonResponse({"status": "success", "message": "You have been checked in successfully!"})

        except Event.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Invalid event."})
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"Error: {str(e)}"})

    return JsonResponse({"status": "error", "message": "Unauthorized or invalid request."})
