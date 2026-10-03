"""Routes: the health check, the admin, the API schema and each app's API."""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView

from apps.core.views import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/", include("apps.notes.urls")),
{%- if cookiecutter.ml_pytorch == "yes" %}
    path("api/", include("apps.inference.urls")),
{%- endif %}
]
