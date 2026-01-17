from django.utils import timezone
from .models import Note
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


def last_notes_for_med(med_id: int, limit=10):
    notes = Note.objects.filter(medication_id=med_id).order_by("-created_at")
    result = []
    for n in notes[:limit]:
        if n.text is not None:
            result.append(n.text)
    return result


def days_since(date):
    now = timezone.now()
    delta = now.date() - date
    return delta.days

router = DefaultRouter()
router.register(r'medications', views.MedicationViewSet, basename='medication')
router.register(r'doselogs', views.DoseLogViewSet, basename='doselog')
router.register(r'notes', views.NoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
]