from swagger_server.test import BaseTestCase
from swagger_server.controllers.survey_response import UPLOAD_SUCCESSFUL
from six import BytesIO
from uuid import uuid4

END_POINT_URL = '/collection-instrument-api/1.0.2/survey_responses/'


class TestRespondentController(BaseTestCase):
    """ RespondentController integration test """

    def test_survey_responses_case_id_post(self):
        # Given a survey response
        data = dict(file=(BytesIO(b'some file data'), 'test.xlsx'))
        case_id = 'befebe93-dd23-453b-99d2-f3014a5010d8'

        # When the file is posted to the end point with a case_id
        response = self.client.open(END_POINT_URL + '{}'.format(case_id),
                                    method='POST', data=data, content_type='multipart/form-data')

        # Then the file uploads successfully
        self.assert200(response)
        self.assertEquals(UPLOAD_SUCCESSFUL, response.data.decode("utf-8"))

    def test_survey_responses_case_id_get(self):
        # Given a survey response is in the database
        data = dict(file=(BytesIO(b'some file data'), 'test.xlsx'))
        case_id = str(uuid4())
        url = END_POINT_URL + '{}'.format(case_id)
        self.client.open(url, method='POST', data=data, content_type='multipart/form-data')

        # When the search is conducted with the case_id
        response = self.client.open(url, method='GET')

        # Then the response contains the survey response
        self.assert200(response)


if __name__ == '__main__':
    import unittest
    unittest.main()
