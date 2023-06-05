from unittest.mock import patch

import requests
import requests_mock
from requests.models import Response

from application.controllers.service_helper import (
    collection_exercise_instrument_update_request,
    service_request,
)
from application.exceptions import RasError, ServiceUnavailableException
from tests.test_client import TestClient

SERVICE = "survey-service"
COLLECTION_EXERCISE_LINK_URL = "http://localhost:8145/collection-instrument/link"
COLLECTION_EXERCISE_ID = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"


class TestServiceHelper(TestClient):
    def test_service_request(self):
        # Given an external service is configured to return a 200
        mock_response = Response()
        mock_response.status_code = 200

        # When a call is made to the service
        with patch("requests.get", return_value=mock_response):
            response = service_request(
                service=SERVICE, endpoint="surveys", search_value="41320b22-b425-4fba-a90e-718898f718ce"
            )

            # Then it response is successful
            self.assertStatus(response, 200)

    def test_incorrect_service_request(self):
        # Given an incorrect Service key
        service = "INCORRECT SERVICE KEY"
        # When a call is made to the service
        # Then a RasError is raised
        with self.assertRaises(RasError):
            service_request(service=service, endpoint="missing_end_point", search_value="")

    def test_service_request_http_error(self):
        # Given an external service is configured to return a http error (404)
        mock_response = Response()
        mock_response.status_code = 404

        # When a call is made to the service
        # Then a RasError is raised
        with patch("requests.get", return_value=mock_response):
            with self.assertRaises(RasError) as exception:
                service_request(
                    service=SERVICE, endpoint="surveys", search_value="41320b22-b425-4fba-a90e-718898f718ce"
                )

        self.assertEqual(["survey-service returned a HTTPError"], exception.exception.errors)
        self.assertEqual(500, exception.exception.status_code)

    def test_service_request_connection_error(self):
        # Given an external service is configured to return a connection error
        # When a call is made to the service
        # Then a ServiceUnavailableException is raised with a 503
        with patch("requests.get", side_effect=requests.ConnectionError):
            with self.assertRaises(ServiceUnavailableException) as exception:
                service_request(
                    service=SERVICE, endpoint="surveys", search_value="41320b22-b425-4fba-a90e-718898f718ce"
                )

        self.assertEqual(["survey-service returned a connection error"], exception.exception.errors)
        self.assertEqual(503, exception.exception.status_code)

    def test_service_request_timeout_error(self):
        # Given an external service is configured to return a Timeout error
        # When a call is made to the service
        # Then a ServiceUnavailableException is raised with a 504
        with patch("requests.get", side_effect=requests.Timeout):
            with self.assertRaises(ServiceUnavailableException) as exception:
                service_request(service=SERVICE, endpoint="surveys", search_value="test_case")
        self.assertEqual(["survey-service has timed out"], exception.exception.errors)
        self.assertEqual(504, exception.exception.status_code)

    @requests_mock.mock()
    def test_publish_uploaded_collection_instrument(self, mock_request):
        # Given a 200 response from the collection exercise service is mocked
        mock_request.post(COLLECTION_EXERCISE_LINK_URL, status_code=200)
        # When a message is posted to that service
        result = collection_exercise_instrument_update_request(COLLECTION_EXERCISE_ID)
        # Then the service responds correctly
        self.assertEqual(result.status_code, 200)

    @requests_mock.mock()
    def test_publish_uploaded_collection_instrument_fails(self, mock_request):
        # Given a 500 response from the collection exercise service is mocked
        mock_request.post(COLLECTION_EXERCISE_LINK_URL, status_code=500)
        # When a message is posted to that service
        # Then a RasError is raised
        with self.assertRaises(RasError):
            collection_exercise_instrument_update_request(COLLECTION_EXERCISE_ID)
