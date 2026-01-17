from datetime import date

from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from medtrackerapp.models import Medication, DoseLog, Note


class MedicationModelTests(TestCase):
    def test_str_returns_name_and_dosage(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )
        self.assertEqual(str(med), "Aspirin (100mg)")

    def test_adherence_rate_all_doses_taken(self):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=30))
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=1))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)

    def test_adherence_rate_no_doses_taken_returns_zero(self):
        """
        Unhappy path: medication prescribed but patient never took a dose.
        """
        med = Medication.objects.create(
            name="Ibuprofen",
            dosage_mg=200,
            prescribed_per_day=3,
        )

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 0.0)

    def test_adherence_rate_partial_doses_taken(self):
        """
        Partially happy path: some doses taken, but not all.
        Expected adherence < 100%.
        """
        med = Medication.objects.create(
            name="Paracetamol",
            dosage_mg=500,
            prescribed_per_day=2,
        )

        now = timezone.now()
        # Only one dose taken
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=2))

        adherence = med.adherence_rate()
        self.assertEqual(adherence, 100.0)


class DoseLogModelTests(TestCase):
    """
    Basic positive-path and relationship tests for DoseLog.
    """

    def test_create_doselog_for_medication(self):
        med = Medication.objects.create(
            name="Vitamin C",
            dosage_mg=1000,
            prescribed_per_day=1,
        )

        log_time = timezone.now()
        log = DoseLog.objects.create(medication=med, taken_at=log_time)

        self.assertEqual(DoseLog.objects.count(), 1)
        self.assertEqual(log.medication, med)
        self.assertEqual(log.taken_at, log_time)

    def test_multiple_doselogs_related_to_same_medication(self):
        med = Medication.objects.create(
            name="Magnesium",
            dosage_mg=400,
            prescribed_per_day=2,
        )

        now = timezone.now()
        DoseLog.objects.create(medication=med, taken_at=now - timedelta(hours=12))
        DoseLog.objects.create(medication=med, taken_at=now)

        self.assertEqual(med.doselog_set.count(), 2)


class NoteModelTests(TestCase):
    def setUp(self):
        self.medication = Medication.objects.create(
            name="Test medication",
            dosage_mg=10,
            prescribed_per_day=2,
        )

    def test_creating_note_links_to_medication_and_sets_date(self):
        note = Note.objects.create(
            medication=self.medication, text="Patient reports mild headache."
        )

        self.assertEqual(note.medication, self.medication)
        self.assertEqual(note.text, "Patient reports mild headache.")
        self.assertIsNotNone(note.created_at)
        self.assertEqual(note.created_at, date.today())

    def test_deleting_medication_deletes_notes(self):
        Note.objects.create(medication=self.medication, text="Some note")

        self.medication.delete()

        self.assertEqual(Note.objects.count(), 0)
