import jwt
import unittest
import requests
from os import putenv

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends.openssl.backend import backend
from swagger_server.controllers.cryptography.keys import TEST_PRIVATE_SIGNING_KEY_PASSWORD, \
    TEST_SDX_PRIVATE_KEY, TEST_PUBLIC_ENCRYPTION_KEY
from swagger_server.controllers.survey_response import SurveyResponse, INVALID_UPLOAD, UPLOAD_SUCCESSFUL, \
    FILE_NAME_LENGTH_ERROR, FILE_EXTENSION_ERROR, UPLOAD_UNSUCCESSFUL
from swagger_server.controllers.cryptography.jwe_decryption import JWERSAOAEPDecryptor
from swagger_server.controllers.exceptions import UploadException
from werkzeug.datastructures import FileStorage
from requests.models import Response
from unittest.mock import patch, Mock
from unittest.mock import MagicMock

TEST_FILE_LOCATION = 'swagger_server/test/test.xlsx'


class TestSurveyResponse(unittest.TestCase):
    """ Survey response unit tests"""

    def setUp(self):
        self.survey_response = SurveyResponse()
        putenv('API_GATEWAY_CASE_URL', 'test')
        putenv('API_GATEWAY_COLLECTION_EXERCISE_URL', 'test')
        putenv('RABBITMQ_LABEL', 'test')

    def test_add_survey_response_success(self):

        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')
            self.survey_response._get_case = MagicMock(return_value=self.mock_get_case_data())
            self.survey_response._get_collection_exercise = MagicMock(return_value=self.mock_get_collection_data())

        # When the file is posted to the upload end point with a case_id
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'
            env = Mock()
            service = Mock()
            service.credentials = {'uri': 'test-uri'}
            env.get_service = Mock(return_value=service)
            with patch('swagger_server.controllers.survey_response.RabbitMQSubmitter'):
                status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file uploads successfully
        self.assertEquals(status, 200)
        self.assertEquals(UPLOAD_SUCCESSFUL, msg)

    def test_add_survey_response_success_check_file_name(self):
        # Given a survey file name of
        ru = '60218763103'
        exercise_ref = '201706'
        survey_id = '221'
        file_extension = 'xls'

        # Calculate the file name
        my_file_name = self.survey_response._generate_file_name(ru, exercise_ref, survey_id, file_extension)

        # File name should look something like this: 60218763103X_201706_221_20170905113039.xls
        # Check we are delimited by underscores and have 4 components i.e. ABC_DEV_EFG_HIJ
        file_components = my_file_name.split('_')
        self.assertEqual(len(file_components), 4)

        # Check our values
        self.assertEqual(file_components[0][0:-1], ru)
        self.assertEqual(file_components[0][-1], 'X')               # This checks default check letter exists
        self.assertEqual(file_components[1], exercise_ref)
        self.assertEqual(file_components[2], survey_id)
        self.assertEqual(file_components[3][-3:], file_extension)   # Check 'xls'
        self.assertEqual(file_components[3][-4:-3], '.')            # Check we have the dot '.'
        print("**** file name is: {} *****".format(my_file_name))

    def test_add_survey_response_missing_file(self):
        # Given a survey response with no file attached
        file = None
        case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'

        # When the file is posted to the end point with a case_id
        status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and a warning message
        self.assertEquals(status, 400)
        self.assertEquals(INVALID_UPLOAD, msg)

    def test_add_survey_response_missing_case_id(self):
        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')

            # When the file is posted to the end point without a case_id
            case_id = None
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and an incomplete upload error
        self.assertEquals(status, 400)
        self.assertEquals(INVALID_UPLOAD, msg)

    def test_add_survey_response_failure_cant_find_case_in_service(self):

        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')

            # When the file is posted to the upload end point with a case_id that doesn't exist in the case service
            case_id = 'b548d78-c2f1-400f-9899-79d944b87300'
            self.survey_response._get_case = self.mock_get_case_data_none
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then survey response causes an invalid upload
        self.assertEquals(status, 400)
        self.assertEquals(INVALID_UPLOAD, msg)

    def test_add_survey_response_failure_cant_find_collection_in_service(self):

        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')
            self.survey_response._get_case = MagicMock(return_value=self.mock_get_case_data())

        # When the file is posted to the end point with a collection exercise that doesn't exist
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'

            self.survey_response._get_collection_exercise = self.mock_get_collection_none
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then survey response causes an invalid upload
        self.assertEquals(status, 400)
        self.assertEquals(INVALID_UPLOAD, msg)

    def test_add_survey_response_send_message_failure(self):

        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.xlsx')
            self.survey_response._get_case = MagicMock(return_value=self.mock_get_case_data())
            self.survey_response._get_collection_exercise = MagicMock(return_value=self.mock_get_collection_data())

            # When the file is posted to the end with a mocked failing rabbit send message
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'

            rabbit = Mock()
            rabbit.send_message = Mock(return_value=False)
            env = Mock()
            service = Mock()
            service.credentials = {'uri': 'test-uri'}
            env.get_service = Mock(return_value=service)

            with patch('swagger_server.controllers.survey_response.RabbitMQSubmitter', return_value=rabbit):
                status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the upload is unsuccessful
        self.assertEquals(status, 500)
        self.assertEquals(UPLOAD_UNSUCCESSFUL, msg)

    def test_add_survey_response_long_file_name(self):
        # Given a survey response
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='abcdefghijklmnopqrstuvwxyzabcdefghijklmnopqrstuvwxyz.xlsx')

            # When the file is posted to the end point with a case_id
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and file name length error
        self.assertEquals(status, 400)
        self.assertEquals(FILE_NAME_LENGTH_ERROR, msg)

    def test_add_survey_response_file_extension(self):

        # Given a survey response with an un-accepted file extension
        with open(TEST_FILE_LOCATION, 'rb') as io:
            file = FileStorage(stream=io, filename='test.test')

            # When the file is posted to the end point with a case_id
            case_id = 'ab548d78-c2f1-400f-9899-79d944b87300'
            status, msg = self.survey_response.add_survey_response(case_id, file)

        # Then the file fails to upload, returning 400 and file type error
        self.assertEquals(status, 400)
        self.assertEquals(FILE_EXTENSION_ERROR, msg)

    def test_missing_case(self):

        # Given a mocked response status code 404
        mock_response = Response()
        mock_response.status_code = 404

        # When a call is made to the case request
        with patch('requests.get', return_value=mock_response):
            case = self.survey_response._get_case('missing case')

            # Then a case is not returned (None)
            self.assertIsNone(case)

    def test_missing_collection_exercise(self):

        # Given a mocked response status code 404
        mock_response = Response()
        mock_response.status_code = 404

        # When a call is made to the collection exercise request
        with patch('requests.get', return_value=mock_response):
            collection_exercise = self.survey_response._get_collection_exercise('missing collection exercise')

            # Then a collection_exercise is not returned (None)
            self.assertIsNone(collection_exercise)

    def test_get_case(self):

        # Given a mocked response
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = b'{"case":"test"}'

        # When a call is made to the case request
        with patch('requests.get', return_value=mock_response):
            case = self.survey_response._get_case('missing case')

            # Then a case is returned
            self.assertEquals(case, {'case': 'test'})

    def test_get_collection_exercise(self):

        # Given a mocked response
        mock_response = Response()
        mock_response.status_code = 200
        mock_response._content = b'{"collection":"test"}'

        # When a call is made to the collection exercise request
        with patch('requests.get', return_value=mock_response):
            collection_exercise = self.survey_response._get_collection_exercise('missing collection exercise')

            # Then a collection_exercise is returned
            self.assertEquals(collection_exercise, {'collection': 'test'})

    def test_gateway_request_success(self):

        # Given a mocked response status code 200
        mock_response = Response()
        mock_response.status_code = 200

        # When a call is made to the gateway
        with patch('requests.get', return_value=mock_response):
            response = self.survey_response._gateway_request('http://test_success_gateway.gov.uk')

            # Then a response code 200 is returned
            self.assertEquals(response.status_code, 200)

    def test_gateway_request_fail(self):

        # Given a patched side effect to a request
        with patch('requests.get', side_effect=requests.exceptions.RequestException):

            # When a call to the gateway is made
            # Then a request exception is raised
            with self.assertRaises(UploadException):
                self.survey_response._gateway_request('http://test_failure_gateway.gov.uk')

    def test_create_jwe_for_file(self):
        # Given a json message
        json = {'file': 'file_as_string', 'file_name': 'file_name'}

        # When it is encrypted using jwe and then decrypted
        jwe = self.survey_response._encrypt_message(json)
        decrypter = Decrypter()
        message = decrypter.decrypt(jwe)

        # Then it is the same message
        self.assertEquals(message, json)

    @staticmethod
    def mock_get_jwt_value():
        return 'invalid jwt'

    @staticmethod
    def mock_get_case_data():
        return {'id': 'ab548d78-c2f1-400f-9899-79d944b87300',
                'state': 'INACTIONABLE',
                'iac': None,
                'actionPlanId': '0009e978-0932-463b-a2a1-b45cb3ffcb2a',
                'collectionInstrumentId': '40c7c047-4fb3-4abe-926e-bf19fa2c0a1e',
                'partyId': 'db036fd7-ce17-40c2-a8fc-932e7c228397',
                'sampleUnitType': 'BI',
                'createdBy': 'SYSTEM',
                'createdDateTime': '2017-07-11T08:35:01.872+0000',
                'responses': [{'inboundChannel': 'OFFLINE', 'dateTime': '2017-07-12T10:47:41.964+0000'},
                              {'inboundChannel': 'OFFLINE', 'dateTime': '2017-07-12T11:28:36.261+0000'},
                              {'inboundChannel': 'OFFLINE', 'dateTime': '2017-07-12T12:24:14.994+0000'}],
                'caseGroup': {'collectionExerciseId': '14fb3e68-4dca-46db-bf49-04b84e07e77c',
                              'id': '9a5f2be5-f944-41f9-982c-3517cfcfef3c',
                              'partyId': '3b136c4b-7a14-4904-9e01-13364dd7b972',
                              'sampleUnitRef': '49900000000',
                              'sampleUnitType': 'B'},
                'caseEvents': None}

    @staticmethod
    def mock_get_collection_data():
        return {'executedBy': None,
                'periodStartDateTime': '2017-09-07T23:00:00.000+0000',
                'scheduledExecutionDateTime': None,
                'scheduledReturnDateTime': None,
                'id': '14fb3e68-4dca-46db-bf49-04b84e07e77c',
                'surveyId': 'cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87',
                'caseTypes': [{'sampleUnitType': 'B', 'actionPlanId': 'e71002ac-3575-47eb-b87f-cd9db92bf9a7'},
                              {'sampleUnitType': 'BI', 'actionPlanId': '0009e978-0932-463b-a2a1-b45cb3ffcb2a'}],
                'scheduledEndDateTime': '2099-01-01T00:00:00.000+0000',
                'state': 'INIT',
                'actualExecutionDateTime': None,
                'actualPublishDateTime': None,
                'name': 'BRES_2016',
                'periodEndDateTime': '2017-09-08T22:59:59.000+0000',
                'scheduledStartDateTime': '2017-08-29T23:00:00.000+0000'}

    @staticmethod
    def mock_get_case_data_none(case_id):
        return None

    @staticmethod
    def mock_get_collection_none(collection_id):
        return None


class Decrypter(JWERSAOAEPDecryptor):
    """ A class used for just testing decryption"""
    def __init__(self):
        super().__init__(TEST_SDX_PRIVATE_KEY, TEST_PRIVATE_SIGNING_KEY_PASSWORD)
        self.rrm_public_key = serialization.load_pem_public_key(
            TEST_PUBLIC_ENCRYPTION_KEY.encode(),
            backend=backend
        )

    def decrypt(self, token):
        signed_token = super().decrypt(token)
        return jwt.decode(signed_token, self.rrm_public_key, algorithms=['RS256'])