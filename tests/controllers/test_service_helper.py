from unittest.mock import patch

import requests
from requests.models import Response

from application.controllers.service_helper import service_request
from application.exceptions import RasError, ServiceUnavailableException
from tests.test_client import TestClient

SERVICE = "survey-service"


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

        self.assertEquals(["survey-service returned a HTTPError"], exception.exception.errors)
        self.assertEquals(500, exception.exception.status_code)

    def test_service_request_connection_error(self):
        # Given an external service is configured to return a connection error
        # When a call is made to the service
        # Then a ServiceUnavailableException is raised with a 503
        with patch("requests.get", side_effect=requests.ConnectionError):
            with self.assertRaises(ServiceUnavailableException) as exception:
                service_request(
                    service=SERVICE, endpoint="surveys", search_value="41320b22-b425-4fba-a90e-718898f718ce"
                )

        self.assertEquals(["survey-service returned a connection error"], exception.exception.errors)
        self.assertEquals(503, exception.exception.status_code)

    def test_service_request_timeout_error(self):
        # Given an external service is configured to return a Timeout error
        # When a call is made to the service
        # Then a ServiceUnavailableException is raised with a 504
        with patch("requests.get", side_effect=requests.Timeout):
            with self.assertRaises(ServiceUnavailableException) as exception:
                service_request(service=SERVICE, endpoint="surveys", search_value="test_case")
        self.assertEquals(["survey-service has timed out"], exception.exception.errors)
        self.assertEquals(504, exception.exception.status_code)
