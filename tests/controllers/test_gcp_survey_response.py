import io
import json
import os
from unittest import TestCase
from unittest.mock import MagicMock

import responses
from requests.exceptions import HTTPError

from application.controllers.gcp_survey_response import (
    FileTooSmallError,
    GcpSurveyResponse,
    SurveyResponseError,
)
from run import create_app

project_root = os.path.dirname(os.path.dirname(__file__))

with open(f"{project_root}/test_data/case_without_case_group.json") as fp:
    case_without_case_group = json.load(fp)


class TestGcpSurveyResponse(TestCase):
    """Survey response unit tests"""

    app = create_app("TestingConfig", False, False)
    file_name = "file_name"
    tx_id = "abb3edd9-21d7-4389-886a-587e4c186a99"
    survey_ref = "066"
    exercise_ref = "25907972-535f-467f-92de-e9fe88fbdd20"
    ru = "11110000001"

    bucket_content = {
        "filename": file_name,
        "file": "file_as_string",
        "case_id": "87daf1b0-c1ae-437e-bddf-dc893eb1059a",
        "survey_id": survey_ref,
    }

    pubsub_payload = {
        "filename": file_name,
        "tx_id": tx_id,
        "survey_id": survey_ref,
        "period": exercise_ref,
        "ru_ref": ru,
        "md5sum": "md5hash",
        "sizeBytes": "1234",
    }

    config = {
        "SEFT_BUCKET_NAME": "test-bucket",
        "SEFT_PUBSUB_PROJECT": "test-project",
        "SEFT_PUBSUB_TOPIC": "test-topic",
    }

    url_get_case_by_id = f"{app.config['CASE_URL']}/cases/{bucket_content['case_id']}"

    def test_is_file_size_too_small(self):
        survey_response = GcpSurveyResponse(self.config)
        test_file_contents = io.BytesIO().read()
        with self.assertRaises(FileTooSmallError):
            survey_response.add_survey_response("id", test_file_contents, "filename", "survey_ref")

    @responses.activate
    def test_failed_api_call_raises_http_exception(self):
        responses.add(responses.GET, self.url_get_case_by_id, status=500)
        with self.app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(HTTPError):
                survey_response.create_pubsub_payload(
                    self.bucket_content["case_id"],
                    self.pubsub_payload["md5sum"],
                    self.bucket_content,
                    "filename",
                    self.tx_id,
                )

    @responses.activate
    def test_missing_data_raises_survey_response_error(self):
        responses.add(responses.GET, self.url_get_case_by_id, json=case_without_case_group)
        with self.app.app_context():
            survey_response = GcpSurveyResponse(self.config)
            with self.assertRaises(SurveyResponseError) as e:
                survey_response.create_pubsub_payload(
                    self.bucket_content["case_id"],
                    self.pubsub_payload["md5sum"],
                    self.bucket_content,
                    "filename",
                    self.tx_id,
                )

            self.assertEqual(e.exception.args[0], "Case group not found")

    def test_missing_filename_raises_key_error(self):
        survey_response = GcpSurveyResponse(self.config)
        test_file_contents = "test file contents"
        survey_response.storage_client = MagicMock()
        filename = ""
        with self.app.app_context():
            with self.assertRaises(ValueError):
                survey_response.put_file_into_gcp_bucket(test_file_contents, filename)

    def test_successful_send_to_pub_sub(self):
        with self.app.app_context():
            publisher = MagicMock()
            publisher.topic_path.return_value = "projects/test-project/topics/test-topic"
            survey_response = GcpSurveyResponse(self.config)
            survey_response.publisher = publisher
            result = survey_response.put_message_into_pubsub(self.pubsub_payload, self.tx_id)
            data = json.dumps(self.pubsub_payload).encode()

            publisher.publish.assert_called()
            publisher.publish.assert_called_with("projects/test-project/topics/test-topic", data=data, tx_id=self.tx_id)
            self.assertIsNone(result)
