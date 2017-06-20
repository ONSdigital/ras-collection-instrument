import unittest
from swagger_server.controllers.survey_response import SurveyResponse, INCOMPLETE_UPLOAD, UPLOAD_SUCCESSFUL, \
    FILE_NAME_LENGTH_ERROR, FILE_TYPE_ERROR, SURVEY_RESPONSE_NOT_FOUND
from werkzeug.datastructures import FileStorage


TEST_FILE_LOCATION = 'swagger_server/test/test.xlsx'


class TestSurveyResponse(unittest.TestCase):
    """ Survey response unit tests"""

    def setUp(self):
        self.survey_response = SurveyResponse()

    def test_add_survey_response_success(self):
        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')

        # When the file is posted to the end point with a case_id
            case_id = 'befebe93-dd23-453b-99d2-f3014a5010d0'
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file uploads successfully
        self.assertEquals(status, 200)
        self.assertEquals(UPLOAD_SUCCESSFUL, msg)

    def test_add_survey_response_missing_file(self):
        # Given a survey response with no file attached
        file = None
        case_id = 'befebe93-dd23-453b-99d2-f3014a5010d1'

        # When the file is posted to the end point with a case_id
        status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and a warning message
        self.assertEquals(status, 400)
        self.assertEquals(INCOMPLETE_UPLOAD, msg)

    def test_add_survey_response_missing_case_id(self):
        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')

            # When the file is posted to the end point without a case_id
            case_id = None
            status, msg = self.survey_response.add_survey_response(case_id, file)

            # Then the file fails to upload, returning 400 and a warning message
        self.assertEquals(status, 400)
        self.assertEquals(INCOMPLETE_UPLOAD, msg)

    def test_add_survey_response_long_file_name(self):
        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz.xlsx')

            # When the file is posted to the end point with a case_id
            case_id = 'befebe93-dd23-453b-99d2-f3014a5010d2'
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and a warning message
        self.assertEquals(status, 400)
        self.assertEquals(FILE_NAME_LENGTH_ERROR, msg)

    def test_add_survey_response_file_extension(self):
        # Given a survey response with an un-accepted file extension
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.test')

            # When the file is posted to the end point with a case_id
            case_id = 'befebe93-dd23-453b-99d2-f3014a5010d3'
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and a warning message
        self.assertEquals(status, 400)
        self.assertEquals(FILE_TYPE_ERROR, msg)

    def test_get_survey_response(self):
        # Given a survey response is in the database
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')
            case_id = 'befebe93-dd23-453b-99d2-f3014a5010d5'
            self.survey_response.add_survey_response(case_id, file)

        # When the file is searched for with a case_id
        case_id = 'befebe93-dd23-453b-99d2-f3014a5010d0'
        status, msg = self.survey_response.get_survey_response(case_id)

        # Then the record is found successfully and returned a json
        self.assertEquals(status, 200)
        self.assertEquals('test.xlsx', msg['file_name'])

    def test_get_survey_response_not_found(self):
        # Given a survey response which doesn't exist
        case_id = 'befebe93-dd23-453b-99d2-f3014a5010d6'

        # When a search is conducted using the case_id
        status, msg = self.survey_response.get_survey_response(case_id)

        # Then the file is not found
        self.assertEquals(status, 404)
        self.assertEquals(SURVEY_RESPONSE_NOT_FOUND, msg)
