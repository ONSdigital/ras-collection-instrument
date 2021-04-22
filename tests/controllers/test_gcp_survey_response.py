import io
import json
import os

from unittest import TestCase
import responses
from requests.exceptions import HTTPError

from application.controllers.gcp_survey_response import GcpSurveyResponse, FileTooSmallError, SurveyResponseError
from run import create_app

project_root = os.path.dirname(os.path.dirname(__file__))

with open(f'{project_root}/test_data/case_without_case_group.json') as fp:
    case_without_case_group = json.load(fp)


class TestGcpSurveyResponse(TestCase):
    """ Survey response unit tests"""

    tx_id = "abb3edd9-21d7-4389-886a-587e4c186a99"

    app = create_app('TestingConfig', False, False)

    bucket_content = {
        'filename': 'file_name',
        'file': 'file_as_string',
        'case_id': '87daf1b0-c1ae-437e-bddf-dc893eb1059a',
        'survey_id': '066'
    }

    config = {
        'SEFT_BUCKET_NAME': 'bucket',
        'GOOGLE_CLOUD_PROJECT': 'project',
        'SEFT_PUBSUB_TOPIC': 'topic'
    }

    def test_is_file_size_too_small(self):
        survey_response = GcpSurveyResponse(self.config)
        test_file_contents = io.BytesIO().read()
        with self.assertRaises(FileTooSmallError):
            survey_response.add_survey_response('id', test_file_contents, 'filename', 'survey_ref')

    @responses.activate
    def test_failed_api_call_raises_http_exception(self):
        responses.add(responses.GET,
                      f"{self.app.config['CASE_URL']}/cases/{self.bucket_content['case_id']}",
                      status=500)
        with self.app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(HTTPError):
                survey_response.create_pubsub_payload(self.bucket_content, self.tx_id)

    @responses.activate
    def test_missing_data_raises_survey_response_error(self):
        responses.add(responses.GET,
                      f"{self.app.config['CASE_URL']}/cases/{self.bucket_content['case_id']}",
                      json=case_without_case_group)
        with self.app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(SurveyResponseError) as e:
                survey_response.create_pubsub_payload(self.bucket_content, self.tx_id)

            self.assertEqual(e.exception.args[0], "Case group not found")
