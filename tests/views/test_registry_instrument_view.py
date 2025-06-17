import base64
import json
from pathlib import Path
from unittest.mock import patch

from flask import current_app

from tests.test_client import TestClient

api_root = "/collection-instrument-api/1.0.2"
exercise_id = "c3c0403a-6e9c-46f6-af5e-5f67fefb2a9d"


class TestRegistryInstrumentView(TestClient):
    """
    Registry Instrument view unit tests
    """

    def test_get_registry_instruments_returns_200_and_empty_list(self):
        with patch(
            "application.views.registry_instrument_view.RegistryInstrument.get_registry_instruments_by_exercise_id"
        ) as mock_get_registry_instruments_by_exercise_id:
            mock_get_registry_instruments_by_exercise_id.return_value = []
            response = self.client.get(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 200)
            self.assertEqual(response.json, [])
            self.assertEqual(response.headers["Content-Type"], "application/json")
            mock_get_registry_instruments_by_exercise_id.assert_called_once_with(exercise_id)

    def test_get_registry_instruments_returns_200_and_list_of_objects(self):
        with patch(
            "application.views.registry_instrument_view.RegistryInstrument.get_registry_instruments_by_exercise_id"
        ) as mock_get_registry_instruments_by_exercise_id:
            with open(Path(__file__).parent.parent / "test_data" / "registry_instruments.json") as f:
                mock_get_registry_instruments_by_exercise_id.return_value = json.load(f)
            response = self.client.get(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 200)
            self.assertEqual(len(response.json), 2)
            self.assertEqual(response.headers["Content-Type"], "application/json")
            mock_get_registry_instruments_by_exercise_id.assert_called_once_with(exercise_id)

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(
            current_app.config.get("SECURITY_USER_NAME"), current_app.config.get("SECURITY_USER_PASSWORD")
        ).encode("utf-8")
        return {"Authorization": "Basic %s" % base64.b64encode(bytes(auth)).decode("ascii")}
