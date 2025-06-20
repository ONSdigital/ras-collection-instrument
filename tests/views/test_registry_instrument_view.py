import base64
import json
from pathlib import Path
from unittest.mock import patch

from flask import current_app

from tests.test_client import TestClient

api_root = "/collection-instrument-api/1.0.2"
exercise_id = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"
form_type_exists = "0001"
form_type_does_not_exist = "9999"


class TestRegistryInstrumentView(TestClient):
    """
    Registry Instrument view unit tests
    """

    def test_get_registry_instrument_returns_200_and_object(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.get_by_exercise_id_and_formtype"
        ) as mock_get_registry_instrument_by_exercise_id_and_formtype:
            with open(Path(__file__).parent.parent / "test_data" / "registry_instrument.json") as f:
                mock_get_registry_instrument_by_exercise_id_and_formtype.return_value = json.load(f)
            response = self.client.get(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}/formtype/{form_type_exists}",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 200)
            self.assertEqual(len(response.json), 8)  # The 8 fields of a registry instrument
            self.assertEqual(response.headers["Content-Type"], "application/json")
            mock_get_registry_instrument_by_exercise_id_and_formtype.assert_called_once_with(
                exercise_id, form_type_exists
            )

    def test_get_registry_instrument_returns_404(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.get_by_exercise_id_and_formtype"
        ) as mock_get_registry_instrument_by_exercise_id_and_formtype:
            mock_get_registry_instrument_by_exercise_id_and_formtype.return_value = None
            response = self.client.get(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}/formtype/{form_type_does_not_exist}",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 404)
            self.assertEqual(response.data.decode(), "Not Found")  # The 8 fields of a registry instrument
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_get_registry_instrument_by_exercise_id_and_formtype.assert_called_once_with(
                exercise_id, form_type_does_not_exist
            )

    def test_get_registry_instruments_returns_200_and_empty_list(self):
        with patch(
            "application.views.registry_instrument_view.RegistryInstrument.get_by_exercise_id"
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
            "application.views.registry_instrument_view.RegistryInstrument.get_by_exercise_id"
        ) as mock_get_registry_instruments_by_exercise_id:
            with open(Path(__file__).parent.parent / "test_data" / "registry_instruments.json") as f:
                mock_get_registry_instruments_by_exercise_id.return_value = json.load(f)
            response = self.client.get(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 200)
            self.assertEqual(len(response.json), 2)  # The 2 registry instrument objects in the test data
            self.assertEqual(response.headers["Content-Type"], "application/json")
            mock_get_registry_instruments_by_exercise_id.assert_called_once_with(exercise_id)

    def test_successful_delete_registry_instrument_returns_200(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.delete_by_exercise_id_and_formtype"
        ) as mock_delete_registry_instrument_by_exercise_id_and_formtype:
            mock_delete_registry_instrument_by_exercise_id_and_formtype.return_value = True
            response = self.client.delete(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}/formtype/{form_type_exists}",
                headers=self.get_auth_headers(),
            )
            self.assertEqual(response.data.decode(), "Successfully deleted registry instrument")
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_delete_registry_instrument_by_exercise_id_and_formtype.assert_called_once_with(
                exercise_id, form_type_exists
            )

    def test_unsuccessful_delete_registry_instrument_missing_instrument(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.delete_by_exercise_id_and_formtype"
        ) as mock_delete_registry_instrument_by_exercise_id_and_formtype:
            mock_delete_registry_instrument_by_exercise_id_and_formtype.return_value = False
            response = self.client.delete(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}/formtype/{form_type_does_not_exist}",
                headers=self.get_auth_headers(),
            )
            self.assertEqual(response.data.decode(), "Not Found")
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_delete_registry_instrument_by_exercise_id_and_formtype.assert_called_once_with(
                exercise_id, form_type_does_not_exist
            )

    def test_successful_put_new_registry_instrument_returns_201(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.save_for_exercise_id_and_formtype"
        ) as mock_save_registry_instrument_for_exercise_id_and_formtype:
            mock_save_registry_instrument_for_exercise_id_and_formtype.return_value = (True, True)
            with open(Path(__file__).parent.parent / "test_data" / "registry_instrument.json") as f:
                body = json.load(f)
            response = self.client.put(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                data=json.dumps(body),
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 201)
            self.assertEqual(response.data.decode(), "Successfully saved registry instrument")
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_save_registry_instrument_for_exercise_id_and_formtype.assert_called_once()

    def test_successful_put_existing_registry_instrument_returns_200(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.save_for_exercise_id_and_formtype"
        ) as mock_save_registry_instrument_for_exercise_id_and_formtype:
            mock_save_registry_instrument_for_exercise_id_and_formtype.return_value = (True, False)
            with open(Path(__file__).parent.parent / "test_data" / "registry_instrument.json") as f:
                body = json.load(f)
            response = self.client.put(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                data=json.dumps(body),
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 200)
            self.assertEqual(response.data.decode(), "Successfully saved registry instrument")
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_save_registry_instrument_for_exercise_id_and_formtype.assert_called_once()

    def test_unsuccessful_put_registry_instrument_returns_500(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.save_for_exercise_id_and_formtype"
        ) as mock_save_registry_instrument_for_exercise_id_and_formtype:
            mock_save_registry_instrument_for_exercise_id_and_formtype.return_value = (False, None)
            with open(Path(__file__).parent.parent / "test_data" / "registry_instrument.json") as f:
                body = json.load(f)
            response = self.client.put(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                data=json.dumps(body),
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 500)
            self.assertEqual(response.data.decode(), "Registry instrument failed to save successfully")
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")
            mock_save_registry_instrument_for_exercise_id_and_formtype.assert_called_once()

    def test_put_registry_instrument_wrong_payload_returns_400(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.save_for_exercise_id_and_formtype"
        ) as mock_save_registry_instrument_for_exercise_id_and_formtype:
            mock_save_registry_instrument_for_exercise_id_and_formtype.return_value = (False, None)
            response = self.client.put(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                data=json.dumps({"invalid_key": "invalid_value"}),
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 400)
            self.assertIn("Invalid payload keys. Expected", response.data.decode())
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    def test_put_registry_instrument_invalid_json_payload_returns_400(self):
        with patch(
            "application.views.registry_instrument_view." "RegistryInstrument.save_for_exercise_id_and_formtype"
        ) as mock_save_registry_instrument_for_exercise_id_and_formtype:
            mock_save_registry_instrument_for_exercise_id_and_formtype.return_value = (False, None)
            response = self.client.put(
                f"{api_root}/registry-instrument/exercise-id/{exercise_id}",
                data="not_valid_json",
                headers=self.get_auth_headers(),
            )
            self.assertStatus(response, 400)
            self.assertIn("Invalid JSON payload", response.data.decode())
            self.assertEqual(response.headers["Content-Type"], "text/html; charset=utf-8")

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(
            current_app.config.get("SECURITY_USER_NAME"), current_app.config.get("SECURITY_USER_PASSWORD")
        ).encode("utf-8")
        return {"Authorization": "Basic %s" % base64.b64encode(bytes(auth)).decode("ascii")}
