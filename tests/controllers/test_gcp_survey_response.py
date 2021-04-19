import io

from unittest import TestCase

from application.controllers.gcp_survey_response import GcpSurveyResponse, FileTooSmallError


class TestGcpSurveyResponse(TestCase):
    """ Survey response unit tests"""

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
