"""The notes API's routes, under /api/notes/."""

from rest_framework.routers import SimpleRouter

from apps.notes.views import NoteViewSet

router = SimpleRouter()
router.register("notes", NoteViewSet, basename="note")

urlpatterns = router.urls
