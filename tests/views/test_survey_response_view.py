import base64
from unittest.mock import patch

from flask import current_app
from six import BytesIO
from requests.models import Response
from sdc.rabbit.exceptions import PublishMessageError

from application.views.survey_responses_view import UPLOAD_SUCCESSFUL, UPLOAD_UNSUCCESSFUL
from application.views.survey_responses_view import INVALID_UPLOAD, MISSING_DATA
from application.controllers.survey_response import FILE_EXTENSION_ERROR, FILE_NAME_LENGTH_ERROR
from tests.test_client import TestClient


class TestSurveyResponseView(TestClient):
    """ Survey response unit tests"""

    def test_add_survey_response_success(self):

        # Given a file with mocked micro service calls to case, collection and survey
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId",' \
                                     b'"partyId": "partyId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyRef": "123456"}'

        mock_party_service = Response()
        mock_party_service.status_code = 200
        mock_party_service._content = b'{"checkletter": "A"}'

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service,
                                mock_survey_service, mock_party_service]), \
                patch('pika.BlockingConnection'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEquals(response.data.decode(), UPLOAD_SUCCESSFUL)

    def test_add_survey_response_writes_expected_filename_in_log(self):

        # Given a file with mocked micro service calls to case, collection and survey
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId",' \
                                     b'"partyId": "partyId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyRef": "123456"}'

        mock_party_service = Response()
        mock_party_service.status_code = 200
        mock_party_service._content = b'{"checkletter": "A"}'

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service,
                                mock_survey_service, mock_party_service]),\
                patch('application.controllers.rabbit_helper.QueuePublisher'):
            with self.assertLogs(level='INFO') as cm:
                # When that file is post to the survey response end point
                self.client.post(
                    '/survey_response-api/v1/survey_responses/{case_id}'.
                    format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                    data=data,
                    headers=self.get_auth_headers(),
                    content_type='multipart/form-data')

                self.assertIn('123456', cm[1][4])

    def test_add_survey_response_missing_case_data(self):

        # Given a file with no case service information
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 404

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service]),\
                patch('application.controllers.rabbit_helper.QueuePublisher'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data')

            # Then the the missing data response is returned
            self.assertStatus(response, 404)
            self.assertEquals(response.data.decode(), MISSING_DATA)

    def test_add_survey_response_missing_survey_data(self):

        # Given a file with no survey service information
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 404

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service, mock_survey_service]),\
                patch('application.controllers.rabbit_helper.QueuePublisher'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data')

            # Then the the missing data response is returned
            self.assertStatus(response, 404)
            self.assertEquals(response.data.decode(), MISSING_DATA)

    def test_add_survey_response_missing_collection_data(self):

        # Given a file with no collection service information
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 404

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service]),\
                patch('application.controllers.rabbit_helper.QueuePublisher'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data')

            # Then the the missing data response is returned
            self.assertStatus(response, 404)
            self.assertEquals(response.data.decode(), MISSING_DATA)

    def test_add_survey_response_missing_data(self):

        # Given no data (eg file) is added to the post
        data = None

        # When the end point is hit
        response = self.client.post(
            '/survey_response-api/v1/survey_responses/{case_id}'.
            format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
            data=data,
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then an invalid upload is returned
        self.assertStatus(response, 400)
        self.assertEquals(response.data.decode(), INVALID_UPLOAD)

    def test_add_survey_response_success_party_missing_data(self):

        # Given a file with mocked micro service calls to case, collection and survey
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId",' \
                                     b'"partyId": "partyId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyRef": "123456"}'

        mock_party_service = Response()
        mock_party_service.status_code = 404

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service,
                                mock_survey_service, mock_party_service]), \
                patch('pika.BlockingConnection'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data')

            # Then the the missing data response is returned
            self.assertStatus(response, 404)
            self.assertEquals(response.data.decode(), MISSING_DATA)

    def test_add_survey_response_invalid_file_extension(self):

        # Given a file with an unaccepted file extension
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.test'))

        # When that file is post to the survey response end point
        response = self.client.post(
            '/survey_response-api/v1/survey_responses/{case_id}'.
            format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
            data=data,
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then the file uploads successfully
        self.assertStatus(response, 400)
        self.assertEquals(response.data.decode(), FILE_EXTENSION_ERROR)

    def test_add_survey_response_invalid_file_name_length(self):

        # Given a file with mocked micro service calls to case, collection and case
        data = dict(file=(BytesIO(b'upload_test'), 'abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz.xlsx'))

        # When that file is post to the survey response end point
        response = self.client.post(
            '/survey_response-api/v1/survey_responses/{case_id}'.
            format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
            data=data,
            headers=self.get_auth_headers(),
            content_type='multipart/form-data')

        # Then the file uploads successfully
        self.assertStatus(response, 400)
        self.assertEquals(response.data.decode(), FILE_NAME_LENGTH_ERROR)

    def test_add_survey_response_rabbit_exception(self):
        # Given a file with mocked services and failing rabbitmq
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId",' \
                                     b'"partyId": "partyId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyRef": "123456"}'

        mock_party_service = Response()
        mock_party_service.status_code = 200
        mock_party_service._content = b'{"checkletter": "A"}'

        with patch('application.controllers.service_helper.service_request',
                   side_effect=[mock_case_service, mock_collection_service,
                                mock_survey_service, mock_party_service]), \
            patch('application.controllers.rabbit_helper.QueuePublisher.publish_message',
                  side_effect=PublishMessageError):
            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                data=data,
                headers=self.get_auth_headers(),
                content_type='multipart/form-data'
            )

            # Then the file does not upload successfully
            self.assertStatus(response, 500)
            self.assertEquals(response.data.decode(), UPLOAD_UNSUCCESSFUL)

    def test_add_survey_response_missing_auth_details(self):

        # Given a file
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        # When that file is post to the survey response end point without the auth header
        response = self.client.post(
            '/survey_response-api/v1/survey_responses/{case_id}'.
            format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
            data=data,
            content_type='multipart/form-data')

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    def test_add_survey_response_incorrect_auth_details(self):

        # Given a file and incorrect auth details
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))
        auth = "{}:{}".format('incorrect_user_name', 'incorrect_password').encode('utf-8')
        header = {'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")}

        # When that file is post to the survey response end point
        response = self.client.post(
            '/survey_response-api/v1/survey_responses/{case_id}'.
            format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
            data=data,
            headers=header,
            content_type='multipart/form-data')

        # Then a 401 unauthorised is return
        self.assertStatus(response, 401)

    @staticmethod
    def get_auth_headers():
        auth = "{}:{}".format(current_app.config.get('SECURITY_USER_NAME'),
                              current_app.config.get('SECURITY_USER_PASSWORD')).encode('utf-8')
        return {
            'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")
        }
