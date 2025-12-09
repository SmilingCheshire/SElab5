from datetime import date, timedelta

from rest_framework.test import APITestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from unittest.mock import patch


from medtrackerapp.models import Medication, DoseLog


class MedicationViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )

    def test_list_medications_valid_data(self):
        url = reverse("medication-list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["name"], "Aspirin")
        self.assertEqual(response.data[0]["dosage_mg"], 100)

    # --- CREATE ---

    def test_create_medication_valid_data(self):
        url = reverse("medication-list")
        payload = {
            "name": "Ibuprofen",
            "dosage_mg": 200,
            "prescribed_per_day": 3,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Medication.objects.count(), 2)
        self.assertEqual(response.data["name"], "Ibuprofen")

    def test_create_medication_invalid_data_missing_name(self):
        url = reverse("medication-list")
        payload = {
            # "name" missing
            "dosage_mg": 50,
            "prescribed_per_day": 1,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("name", response.data)

    # --- RETRIEVE ---

    def test_retrieve_medication_valid_id(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Aspirin")

    def test_retrieve_medication_invalid_id(self):
        url = reverse("medication-detail", args=[9999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # --- UPDATE ---

    def test_update_medication_valid_data(self):
        url = reverse("medication-detail", args=[self.med.id])
        payload = {
            "name": "Aspirin updated",
            "dosage_mg": 150,
            "prescribed_per_day": 1,
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.med.refresh_from_db()
        self.assertEqual(self.med.name, "Aspirin updated")
        self.assertEqual(self.med.dosage_mg, 150)
        self.assertEqual(self.med.prescribed_per_day, 1)

    def test_update_medication_invalid_data(self):
        url = reverse("medication-detail", args=[self.med.id])
        payload = {
            "name": "",           # invalid
            "dosage_mg": -10,     # invalid
            "prescribed_per_day": 0,
        }

        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # --- DELETE ---

    def test_delete_medication_valid_id(self):
        url = reverse("medication-detail", args=[self.med.id])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Medication.objects.filter(id=self.med.id).exists())

    def test_delete_medication_invalid_id(self):
        url = reverse("medication-detail", args=[9999])
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    
    def test_expected_doses_valid_days(self):
        """
        GET /api/medications/<id>/expected-doses/?days=7
        should return 200 and a JSON with medication_id, days, expected_doses.
        """
        url = reverse("medication-expected-doses", args=[self.med.id])

        response = self.client.get(url, {"days": 7})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["medication_id"], self.med.id)
        self.assertEqual(response.data["days"], 7)
        # expected_doses must be an int
        self.assertIsInstance(response.data["expected_doses"], int)

    def test_expected_doses_missing_days_param_returns_400(self):
        """
        Missing ?days=... should return 400.
        """
        url = reverse("medication-expected-doses", args=[self.med.id])

        response = self.client.get(url)  # no query params

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("days", response.data["detail"].lower())

    def test_expected_doses_non_integer_days_returns_400(self):
        """
        Non-integer days should return 400.
        """
        url = reverse("medication-expected-doses", args=[self.med.id])

        response = self.client.get(url, {"days": "abc"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("integer", response.data["detail"].lower())

    def test_expected_doses_non_positive_days_returns_400(self):
        """
        days <= 0 should return 400.
        """
        url = reverse("medication-expected-doses", args=[self.med.id])

        response = self.client.get(url, {"days": 0})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("positive", response.data["detail"].lower())

    def test_expected_doses_value_error_from_model_returns_400(self):
        """
        If Medication.expected_doses raises ValueError,
        the endpoint should return 400.
        """
        url = reverse("medication-expected-doses", args=[self.med.id])

        with patch.object(Medication, "expected_doses", side_effect=ValueError("boom")):
            response = self.client.get(url, {"days": 5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("boom", response.data["detail"])


class DoseLogViewTests(APITestCase):
    def setUp(self):
        self.med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )

        # one existing log, taken "now"
        self.log_time = timezone.now()
        self.log = DoseLog.objects.create(
            medication=self.med,
            taken_at=self.log_time,
            was_taken=True,
        )

    def test_list_logs(self):
        url = "/api/logs/"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        # field names must match serializer; usually:
        self.assertEqual(response.data[0]["medication"], self.med.id)
        self.assertTrue(response.data[0]["was_taken"])

    def test_create_log_valid_data(self):
        url = "/api/logs/"

        new_time = self.log_time + timedelta(days=1)
        payload = {
            "medication": self.med.id,
            "taken_at": new_time.isoformat(),  # DateTimeField
            "was_taken": False,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DoseLog.objects.count(), 2)

    def test_create_log_invalid_missing_fields(self):
        url = "/api/logs/"

        # missing taken_at and was_taken -> should be 400
        payload = {
            "medication": self.med.id,
        }

        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_logs_valid_range(self):
        # range that includes self.log_time.date()
        start = (self.log_time.date() - timedelta(days=1)).isoformat()
        end = (self.log_time.date() + timedelta(days=1)).isoformat()
        url = f"/api/logs/filter/?start={start}&end={end}"

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_logs_invalid_range(self):
        # end before start – behaviour depends on your view
        start = (self.log_time.date() + timedelta(days=2)).isoformat()
        end = (self.log_time.date() - timedelta(days=2)).isoformat()
        url = f"/api/logs/filter/?start={start}&end={end}"

        response = self.client.get(url)

        # if your view returns 400 for invalid range, this passes;
        # if it returns 200 + empty list, change assertion accordingly:
        self.assertIn(response.status_code, (status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK))
