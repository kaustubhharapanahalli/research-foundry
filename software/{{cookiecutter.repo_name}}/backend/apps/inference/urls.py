"""The inference API's routes, under /api/inference/."""

from django.urls import path

from apps.inference.views import ScoreView

urlpatterns = [
    path("inference/score/", ScoreView.as_view(), name="inference-score"),
]
