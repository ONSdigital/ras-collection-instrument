from swagger_server.test import BaseTestCase
from swagger_server.controllers.survey_response import UPLOAD_SUCCESSFUL
from six import BytesIO
from unittest.mock import patch

END_POINT_URL = '/collection-instrument-api/1.0.2/survey_responses/'


class TestRespondentController(BaseTestCase):
    """ RespondentController integration test """

    def test_survey_responses_case_id_post(self):
        # Given a survey response

        with patch('swagger_server.controllers.survey_response.RabbitMQSubmitter'):

            data = dict(file=(BytesIO(b'some file data'), 'test.xlsx'))
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'

            # When the file is posted to the end point with a case_id
            response = self.client.open(END_POINT_URL + '{}'.format(case_id),
                                        method='POST', data=data, content_type='multipart/form-data')

            # Then the file uploads successfully
            self.assert200(response)
            self.assertEquals(UPLOAD_SUCCESSFUL, response.data.decode("utf-8"))

if __name__ == '__main__':
    import unittest
    unittest.main()
