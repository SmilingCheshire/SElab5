from django.test import TestCase
from unittest.mock import patch, Mock

from medtrackerapp.services import DrugInfoService
from medtrackerapp.models import Medication


class DrugInfoServiceTests(TestCase):
    """
    Tests for the service that calls the external OpenFDA API.
    The real HTTP GET is mocked so the test does not use the network.
    """

    @patch("medtrackerapp.services.requests.get")
    def test_get_drug_info_success(self, mock_get):
        # arrange: fake HTTP response returned by requests.get(...)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [{"id": "123", "drug_name": "aspirin"}]
        }
        mock_get.return_value = mock_response

        # act
        result = DrugInfoService.get_drug_info("aspirin")

        # assert: we got a processed dict with expected keys/values
        self.assertEqual(result["name"], "aspirin")
        self.assertIn("manufacturer", result)
        self.assertIn("purpose", result)
        self.assertIn("warnings", result)

        # depending on your implementation, these defaults should hold:
        self.assertEqual(result["manufacturer"], "Unknown")
        self.assertEqual(result["purpose"], ["Not specified"])
        self.assertEqual(result["warnings"], ["No warnings available"])

        # and GET was called once
        mock_get.assert_called_once()


class MedicationExternalInfoTests(TestCase):
    """
    Tests for Medication.fetch_external_info, which wraps DrugInfoService.
    DrugInfoService.get_drug_info is mocked.
    """

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_returns_service_data(self, mock_get_info):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )
        mock_get_info.return_value = {"some": "data"}

        result = med.fetch_external_info()

        self.assertEqual(result, {"some": "data"})
        mock_get_info.assert_called_once_with("Aspirin")

    @patch("medtrackerapp.models.DrugInfoService.get_drug_info")
    def test_fetch_external_info_handles_exception(self, mock_get_info):
        med = Medication.objects.create(
            name="Aspirin",
            dosage_mg=100,
            prescribed_per_day=2,
        )
        mock_get_info.side_effect = Exception("API error")

        result = med.fetch_external_info()

        self.assertEqual(result, {"error": "API error"})
        mock_get_info.assert_called_once_with("Aspirin")
