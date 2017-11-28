from application.controllers.survey_response import UPLOAD_SUCCESSFUL
from six import BytesIO
from tests.test_client import TestClient
from unittest.mock import patch
from requests.models import Response


class TestSurveyResponseView(TestClient):
    """ Survey response unit tests"""

    def test_add_survey_response_success(self):

        # Given a file with mocked micro service calls to case, collection and case
        data = dict(file=(BytesIO(b'upload_test'), 'upload_test.xls'))

        mock_case_service = Response()
        mock_case_service.status_code = 200
        mock_case_service._content = b'{"caseGroup": {"sampleUnitRef": "sampleUnitRef", ' \
                                     b'"collectionExerciseId": "collectionExerciseId"}}'

        mock_collection_service = Response()
        mock_collection_service.status_code = 200
        mock_collection_service._content = b'{"exerciseRef": "test", "surveyId": "test"}'

        mock_survey_service = Response()
        mock_survey_service.status_code = 200
        mock_survey_service._content = b'{"surveyRef": "123456"}'

        with patch('application.controllers.survey_response.service_request',
                   side_effect=[mock_case_service, mock_collection_service, mock_survey_service]),\
                patch('application.controllers.survey_response.RabbitMQSubmitter'):

            # When that file is post to the survey response end point
            response = self.client.post(
                '/survey_response-api/v1/survey_responses/{case_id}'.
                format(case_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'),
                data=data,
                content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assertStatus(response, 200)
            self.assertEquals(response.data.decode(), UPLOAD_SUCCESSFUL)
