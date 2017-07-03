import os
import requests
import uuid

from datetime import datetime
from ons_ras_common import ons_env
from swagger_server.controllers.helper import is_valid_file_extension, is_valid_file_name_length, \
    convert_file_object_to_string_base64
from swagger_server.controllers.submitter.encrypter import Encrypter
from swagger_server.controllers.submitter.rabbitmq_submitter import RabbitMQSubmitter
from swagger_server.controllers.exceptions import RequestException

FILE_EXTENSION_ERROR = 'un-accepted file extension'
FILE_NAME_LENGTH_ERROR = 'The name of the file is too long'
UPLOAD_SUCCESSFUL = 'Upload successful'
UPLOAD_UNSUCCESSFUL = 'Upload failed'
INVALID_UPLOAD = 'The upload must have valid case_id and a file attached'
QUEUE_NAME = 'Seft.Responses'


class SurveyResponse(object):
    """
    The survey response from a respondent
    """
    def add_survey_response(self, case_id, file):
        """
        Encrypt and upload survey response to rabbitmq
        :param case_id: A case id
        :param file: A file object from which we can read the file contents
        :return: Returns status code and message
        """

        tx_id = str(uuid.uuid4())
        ons_env.logger.info('Adding survey response')

        if case_id and file and hasattr(file, 'filename'):
            file_name, file_extension = os.path.splitext(file.filename)
            is_valid_file, msg = self._is_valid_file(file_name, file_extension)

            if not is_valid_file:
                return 400, msg

            # request case_group from API gateway
            case = self._get_case(case_id)

            if not case or 'caseGroup' not in case:
                return self._invalid_upload()

            case_group = case.get('caseGroup')

            if case_group.get('partyId') != self._get_jwt_value():
                ons_env.logger.debug('The party ID in the case does not match the value in the JWT')
                return self._invalid_upload()

            ru = case_group.get('sampleUnitRef')
            collection_exercise_id = case_group.get('collectionExerciseId')

            # request collection_exercise from API gateway
            collection_exercise = self._get_collection_exercise(collection_exercise_id)

            if collection_exercise:
                period = collection_exercise.get('periodStartDateTime')
                survey_id = collection_exercise.get('surveyId')
            else:
                return self._invalid_upload()

            # Create, encrypt and send message to rabbitmq
            json_message = self._create_json_message_for_file(file, file_extension, period, ru, survey_id)
            encrypted_message = self._encrypt_message(json_message)

            rabbit_mq = RabbitMQSubmitter()

            if rabbit_mq.send_message(encrypted_message, QUEUE_NAME, tx_id):
                return 200, UPLOAD_SUCCESSFUL
            else:
                return 400, UPLOAD_UNSUCCESSFUL
        else:
            ons_env.logger.debug('case id or file missing')
            return self._invalid_upload()

    def _create_json_message_for_file(self, file, file_extension, period, ru, survey_id):
        """
          Create json message from file
          :param file: The file uploaded
          :param file_extension: The file type
          :param period: The period from the collection exercise
          :param ru: reporting unit
          :param survey_id: The survey id
          :return: Returns json message 
        """

        ons_env.logger.info('creating json message')
        file_as_string = convert_file_object_to_string_base64(file)
        generated_file_name = self._generate_file_name(ru, period, survey_id, file_extension)

        message_json = {
            'file_name': generated_file_name,
            'file': file_as_string
        }

        return message_json

    def _get_case(self, case_id):
        """
        Get case details from gateway
        :param case_id: The case_id to search with
        :return: case details
        """

        ons_env.logger.info('Getting case from case service')
        # TODO remove test url
        TEST_CASE_URL = 'http://ras-api-gateway-int.apps.devtest.onsclofo.uk:80/cases/'
        case = None
        url = os.environ.get('API_GATEWAY_CASE_URL', TEST_CASE_URL) + '{}'.format(case_id)

        response = self._gateway_request(url)

        if response.status_code == 200:
            case = response.json()
        else:
            ons_env.logger.error("Case not found")
        return case

    def _get_collection_exercise(self, collection_exercise_id):
        """
        Get collection exercise details from request
        :param collection_exercise_id: The collection_exercise_id to search with
        :return: collection_exercise
        """

        ons_env.logger.info('Getting collection from collection service')
        collection_exercise = None
        # TODO remove test url
        TEST_EXERCISE_URL = 'http://ras-api-gateway-int.apps.devtest.onsclofo.uk:80/collectionexercises/'

        url = os.environ.get('API_GATEWAY_COLLECTION_EXERCISE_URL', TEST_EXERCISE_URL) \
            + '{}'.format(collection_exercise_id)
        response = self._gateway_request(url)
        if response.status_code == 200:
            collection_exercise = response.json()
        else:
            ons_env.logger.debug('Collection Exercise not found')
        return collection_exercise

    @staticmethod
    def _get_jwt_value():
        # TODO to be changed to the cookie value when available
        return '3b136c4b-7a14-4904-9e01-13364dd7b972'

    @staticmethod
    def _invalid_upload():
        """
        Generic status code and message for frontend
        :return: status code, message
        """
        return 400, INVALID_UPLOAD


    @staticmethod
    def _is_valid_file(file_name, file_extension):
        """
        Check a file is valid
        :param file_name: The file_name to check
        :return: boolean
        """

        ons_env.logger.info('checking if file is valid')
        if not is_valid_file_extension(file_extension, ons_env.get('upload_file_extensions')):
            return False, FILE_EXTENSION_ERROR

        if not is_valid_file_name_length(file_name, ons_env.get('max_upload_file_name_length')):
            return False, FILE_NAME_LENGTH_ERROR

        return True, ""

    @staticmethod
    def _encrypt_message(message_json):
        """
        encrypt the JSON message
        :param message_json: The file in json format
        :return: a jwe
        """

        ons_env.logger.info('encrypting json')
        encrypter = Encrypter()
        return encrypter.encrypt(message_json)

    @staticmethod
    def _generate_file_name(ru, period, survey_id, file_extension):
        """
        Generate the file name for the upload
        :param ru: reporting unit
        :param period: The collection period
        :param survey_id: The id of the survey
        :param file_extension: The upload file extension
        :return: file name
        """

        ons_env.logger.info('generating file name for upload')

        time_date_stamp = datetime.now()
        file_name = "{ru}-{survey_id}-{period}-{time_date_stamp}.{file_format}".format(ru=ru,
                                                                                       survey_id=survey_id,
                                                                                       period=period,
                                                                                       time_date_stamp=time_date_stamp,
                                                                                       file_format=file_extension)
        return file_name

    @staticmethod
    def _gateway_request(url):
        """
        The request to the gateway
        :param url: The URL to request from 
        :return: response
        """

        try:
            response = requests.get(url, verify=False)
        except requests.exceptions.RequestException:
            ons_env.logger.error('request failed to connect to {}'.format(url))
            raise RequestException('API gateway unavailable')
        return response
