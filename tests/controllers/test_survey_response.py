import io
from os import putenv, environ
from unittest.mock import patch, Mock

from pika.exceptions import AMQPConnectionError
from werkzeug.datastructures import FileStorage

from application.controllers.survey_response import SurveyResponse
from tests.test_client import TestClient

TEST_FILE_LOCATION = 'tests/files/test.xlsx'

with open("./tests/files/keys.json") as fp:
    environ["JSON_SECRET_KEYS"] = fp.read()


class TestSurveyResponse(TestClient):
    """ Survey response unit tests"""

    def setUp(self):
        self.survey_response = SurveyResponse()
        putenv('CASE_URL', 'tests')
        putenv('COLLECTION_EXERCISE_URL', 'tests')
        putenv('RABBITMQ_LABEL', 'tests')

    def test_initialise_messaging(self):
        with patch('pika.BlockingConnection'):
            self.survey_response.initialise_messaging()

    def test_initialise_messaging_rabbit_fails(self):
        with self.assertRaises(AMQPConnectionError):
            with patch('pika.BlockingConnection', side_effect=AMQPConnectionError):
                self.survey_response.initialise_messaging()

    def test_add_survey_response_success(self):

        # Given a survey response
        filename = 'tests.xlsx'
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename=filename)

        # When the file is posted to the upload end point with a case_id
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'
            env = Mock()
            service = Mock()
            service.credentials = {'uri': 'tests-uri'}
            env.get_service = Mock(return_value=service)
            with patch('pika.BlockingConnection'):
                status = self.survey_response.add_survey_response(case_id, file, filename, '023')

        # Then the file uploads successfully
        self.assertTrue(status)

    def test_is_file_size_too_small(self):
        test_file = io.BytesIO()
        test_file_size = test_file.getbuffer().nbytes
        SurveyResponse.is_file_size_too_small(self, test_file_size)
