from django.urls import path
from .views import (
    active_elections,
    candidate_list,
    cast_vote,
    export_results_excel,
    export_results_pdf,
    live_results,
    verify_results,
    thank_you,
    election_results,
    already_voted,
    self_nominate
)

app_name = "voting"

urlpatterns = [
    path("elections/", active_elections, name="elections"),
    path("elections/<int:election_id>/cast/", cast_vote, name="cast_vote"),
    path("elections/<int:election_id>/position/<int:position_id>/", candidate_list, name="candidates"),
    path("results/<int:election_id>/", election_results, name="results"),
    path("verify/<int:election_id>/", verify_results, name="verify_results"),
    path("elections/<int:election_id>/live-results/", live_results, name="live_results"),

    path("thank-you/", thank_you, name="thank_you"),
    path("already-voted/", already_voted, name="already_voted"),
    path("self-nominate/", self_nominate, name="self_nominate"),
    path('elections/<int:election_id>/export/excel/', export_results_excel, name='export_results_excel'),
    path('elections/<int:election_id>/export/pdf/', export_results_pdf, name='export_results_pdf'),

]
