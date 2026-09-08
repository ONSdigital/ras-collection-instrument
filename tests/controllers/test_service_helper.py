from unittest.mock import MagicMock, patch

import requests

from application.controllers.service_helper import (
    _get_auth,
    _get_json,
    collection_exercise_instrument_update_request,
    fetch_and_apply_oidc_credentials,
    get_cir_metadata,
    get_collection_exercise_by_id,
    get_collection_exercise_id_by_period_and_survey_ref,
    get_survey_details_by_id,
)
from application.exceptions import RasError, ServiceUnavailableException
from tests.test_client import TestClient

COLLECTION_EXERCISE_URL = "http://collection-exercise"
COLLECTION_EXERCISE_ID = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"


class TestServiceHelper(TestClient):
    @patch("application.controllers.service_helper.current_app")
    def test_get_auth(self, mock_current_app):
        mock_current_app.config = {
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }

        result = _get_auth()

        self.assertEqual(result, ("username", "password"))

    @patch("application.controllers.service_helper.requests.post")
    @patch("application.controllers.service_helper.current_app")
    def test_collection_exercise_instrument_update_request(self, mock_current_app, mock_post):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_post.return_value = MagicMock()

        collection_exercise_instrument_update_request("UPDATE", COLLECTION_EXERCISE_ID)

        mock_post.assert_called_once_with(
            f"{COLLECTION_EXERCISE_URL}/collection-instrument/link",
            json={
                "action": "UPDATE",
                "exercise_id": COLLECTION_EXERCISE_ID,
            },
            auth=("username", "password"),
        )

    @patch("application.controllers.service_helper.current_app")
    def test_collection_exercise_instrument_update_request_not_configured(self, mock_current_app):
        mock_current_app.config = {
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }

        with self.assertRaises(RasError) as error:
            collection_exercise_instrument_update_request("UPDATE", COLLECTION_EXERCISE_ID)
        self.assertEqual(error.exception.status_code, 500)

    @patch("application.controllers.service_helper.requests.post")
    @patch("application.controllers.service_helper.current_app")
    def test_collection_exercise_instrument_update_request_http_error(self, mock_current_app, mock_post):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        mock_post.return_value = mock_response

        with self.assertRaises(RasError) as error:
            collection_exercise_instrument_update_request("UPDATE", COLLECTION_EXERCISE_ID)
        self.assertEqual(error.exception.status_code, 500)

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.current_app")
    def test_get_collection_exercise_by_id(self, mock_current_app, mock_get_json):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_get_json.return_value = {"id": COLLECTION_EXERCISE_ID}

        result = get_collection_exercise_by_id(COLLECTION_EXERCISE_ID)

        mock_get_json.assert_called_once_with(
            f"{COLLECTION_EXERCISE_URL}/collectionexercises/{COLLECTION_EXERCISE_ID}",
            "collection exercise",
            auth=("username", "password"),
        )
        self.assertEqual(result, {"id": COLLECTION_EXERCISE_ID})

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.current_app")
    def test_get_survey_details_by_id(self, mock_current_app, mock_get_json):
        mock_current_app.config = {
            "SURVEY_URL": "http://survey",
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_get_json.return_value = {"id": "survey-id", "survey_ref": "123"}

        result = get_survey_details_by_id("survey-id")

        mock_get_json.assert_called_once_with(
            "http://survey/surveys/survey-id",
            "survey",
            auth=("username", "password"),
        )
        self.assertEqual(result, {"id": "survey-id", "survey_ref": "123"})

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.current_app")
    def test_get_collection_exercise_id_by_period_and_survey_ref(self, mock_current_app, mock_get_json):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_get_json.return_value = {"id": COLLECTION_EXERCISE_ID}

        result = get_collection_exercise_id_by_period_and_survey_ref("202601", "123")

        mock_get_json.assert_called_once_with(
            "http://collection-exercise/collectionexercises/202601/survey/123",
            "collection exercise",
            auth=("username", "password"),
        )
        self.assertEqual(result, COLLECTION_EXERCISE_ID)

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.current_app")
    def test_get_collection_exercise_id_by_period_and_survey_ref_not_found(self, mock_current_app, mock_get_json):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }
        mock_get_json.side_effect = RasError("collection exercise returned an HTTP error", 404)

        with self.assertRaisesRegex(ValueError, "Collection exercise not found"):
            get_collection_exercise_id_by_period_and_survey_ref("202601", "123")

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.current_app")
    def test_get_collection_exercise_id_reraises_non_404(self, mock_current_app, mock_get_json):
        mock_current_app.config = {
            "COLLECTION_EXERCISE_URL": COLLECTION_EXERCISE_URL,
            "SECURITY_USER_NAME": "username",
            "SECURITY_USER_PASSWORD": "password",
        }

        mock_get_json.side_effect = RasError(
            "collection exercise returned an HTTP error",
            500,
        )

        with self.assertRaises(RasError) as error:
            get_collection_exercise_id_by_period_and_survey_ref("202601", "123")
        self.assertEqual(error.exception.status_code, 500)

    @patch("application.controllers.service_helper._get_json")
    @patch("application.controllers.service_helper.requests.Session")
    @patch("application.controllers.service_helper.current_app")
    def test_get_cir_metadata(self, mock_current_app, mock_session_class, mock_get_json):
        mock_current_app.config = {
            "CIR_OAUTH2_CLIENT_ID": "cir-client-id",
            "CIR_API_URL": "http://cir",
            "CIR_API_PREFIX": "/v1/instruments",
        }
        mock_session = MagicMock()
        mock_session_class.return_value = mock_session
        cir_metadata = [
            {
                "ci_version": 3,
                "guid": "instrument-guid",
                "published_at": "2026-01-01T12:00:00",
            }
        ]
        mock_get_json.return_value = cir_metadata

        result = get_cir_metadata("0002", "123")

        mock_get_json.assert_called_once_with(
            "http://cir/v1/instruments",
            "CIR",
            session=mock_session,
            params={
                "classifier_type": "form_type",
                "classifier_value": "0002",
                "language": "en",
                "survey_id": "123",
            },
        )
        self.assertEqual(result, cir_metadata)

    @patch("application.controllers.service_helper.current_app")
    def test_fetch_and_apply_oidc_credentials(self, mock_current_app):
        session = MagicMock()
        mock_credentials = MagicMock()
        mock_oidc_credentials_service = MagicMock()
        mock_oidc_credentials_service.get_credentials.return_value = mock_credentials
        mock_current_app.oidc = {
            "oidc_credentials_service": mock_oidc_credentials_service,
        }

        fetch_and_apply_oidc_credentials(
            session=session,
            client_id="cir-client-id",
        )
        mock_oidc_credentials_service.get_credentials.assert_called_once_with(
            iap_client_id="cir-client-id",
        )
        mock_credentials.apply.assert_called_once_with(
            headers=session.headers,
        )

    @patch("application.controllers.service_helper.requests.get")
    def test_get_json(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "123"}
        mock_get.return_value = mock_response

        result = _get_json(
            "http://service/test",
            "test service",
            auth=("username", "password"),
            params={
                "key": "value",
            },
        )

        self.assertEqual(result, {"id": "123"})

    @patch("application.controllers.service_helper.requests.get")
    def test_get_json_http_error(self, mock_get):
        mock_response = MagicMock()

        http_error = requests.HTTPError()
        http_error.response = MagicMock()
        http_error.response.status_code = 404

        mock_response.raise_for_status.side_effect = http_error
        mock_get.return_value = mock_response

        with self.assertRaises(RasError) as error:
            _get_json("http://service/test", "test service")
        self.assertEqual(error.exception.status_code, 404)

    @patch("application.controllers.service_helper.requests.get")
    def test_get_json_connection_error(self, mock_get):
        mock_get.side_effect = requests.ConnectionError()

        with self.assertRaises(ServiceUnavailableException) as error:
            _get_json("http://service/test", "test service")
        self.assertEqual(error.exception.status_code, 503)

    @patch("application.controllers.service_helper.requests.get")
    def test_get_json_timeout(self, mock_get):
        mock_get.side_effect = requests.Timeout()

        with self.assertRaises(ServiceUnavailableException) as error:
            _get_json("http://service/test", "test service")
        self.assertEqual(error.exception.status_code, 504)
