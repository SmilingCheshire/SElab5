from django.utils import timezone
from .models import Note
from django.urls import path
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

urlpatterns = [
    path("notes/", views.note_list, name="note-list"),
    path("notes/<int:pk>/", views.note_detail, name="note-detail"),
]