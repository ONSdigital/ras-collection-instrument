import requests_mock

from application.controllers.service_helper import (
    collection_exercise_instrument_update_request,
)
from application.exceptions import RasError
from tests.test_client import TestClient

SERVICE = "survey-service"
COLLECTION_EXERCISE_LINK_URL = "http://localhost:8145/collection-instrument/link"
COLLECTION_EXERCISE_ID = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"


class TestServiceHelper(TestClient):

    @requests_mock.mock()
    def test_publish_uploaded_collection_instrument_fails(self, mock_request):
        # Given a 500 response from the collection exercise service is mocked
        mock_request.post(COLLECTION_EXERCISE_LINK_URL, status_code=500)
        # When a message is posted to that service
        # Then a RasError is raised
        with self.assertRaises(RasError):
            collection_exercise_instrument_update_request("ADD", COLLECTION_EXERCISE_ID)
