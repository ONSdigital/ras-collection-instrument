from requests.models import Response
from unittest.mock import patch

from application.controllers.service_helper import service_request
from application.exceptions import RasError
from tests.test_client import TestClient


class TestServiceHelper(TestClient):

    def test_service_request(self):
        # Given a configured service
        service = 'case-service'
        mock_response = Response()
        mock_response.status_code = 200

        # When a call is made to the service
        with patch('requests.get', return_value=mock_response):
            response = service_request(service=service, endpoint='cases', search_value='test_case')

            # Then it response successfully
            self.assertStatus(response, 200)

    def test_service_request_failure(self):
        # Given an incorrect Service key
        service = 'INCORRECT SERVICE KEY'
        # When a call is made to the service
        # Then a RasError is raised
        with self.assertRaises(RasError):
            service_request(service=service, endpoint='missing_end_point', search_value='value')
