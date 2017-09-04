import os
import requests
import time
import uuid

from ons_ras_common import ons_env
from swagger_server.controllers.helper import is_valid_file_extension, is_valid_file_name_length, \
    convert_file_object_to_string_base64
from swagger_server.controllers.submitter.encrypter import Encrypter
from swagger_server.controllers.submitter.rabbitmq_submitter import RabbitMQSubmitter
from swagger_server.controllers.exceptions import UploadException

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
            ru = case_group.get('sampleUnitRef')
            exercise_ref = case_group.get('exerciseRef')
            collection_exercise_id = case_group.get('collectionExerciseId')

            # request collection_exercise from API gateway
            collection_exercise = self._get_collection_exercise(collection_exercise_id)

            if collection_exercise:
                exercise_ref = collection_exercise.get('exerciseRef')
                survey_id = collection_exercise.get('surveyId')
            else:
                return self._invalid_upload()

            # Create, encrypt and send message to rabbitmq
            generated_file_name = self._generate_file_name(ru, exercise_ref, survey_id, file_extension)
            json_message = self._create_json_message_for_file(generated_file_name, file, case_id)
            encrypted_message = self._encrypt_message(json_message)

            return self._send_message_to_rabbitmq(encrypted_message, tx_id)

        else:
            ons_env.logger.debug('case id or file missing')
            return self._invalid_upload()

    @staticmethod
    def _create_json_message_for_file(generated_file_name, file, case_id):
        """
          Create json message from file
          :param generated_file_name: The generated file name
          :param file: The file uploaded
          :param case_id: The case UUID
          :return: Returns json message 
        """

        ons_env.logger.info('creating json message')
        file_as_string = convert_file_object_to_string_base64(file)

        message_json = {
            'filename': generated_file_name,
            'file': file_as_string,
            'case_id': case_id
        }

        return message_json

    def _get_case(self, case_id):
        """
        Get case details from gateway
        :param case_id: The case_id to search with
        :return: case details
        """

        ons_env.logger.info('Getting case from case service')
        case = None
        request_url = self._build_request_url('API_GATEWAY_CASE_URL', case_id)
        response = self._gateway_request(request_url)

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
        request_url = self._build_request_url('API_GATEWAY_COLLECTION_EXERCISE_URL', collection_exercise_id)
        response = self._gateway_request(request_url)

        if response.status_code == 200:
            collection_exercise = response.json()
        else:
            ons_env.logger.debug('Collection Exercise not found')
        return collection_exercise

    @staticmethod
    def _build_request_url(service_url_key, search_value):
        """
        Builds the request url from the service url and the search param
        :param service_url_key: environmental variable key
        :param search_value: The value to add to the end of the url, the value to search for
        :return: url string
        """
        request_url = os.getenv(service_url_key, ons_env.get(service_url_key))

        if request_url:
            return request_url + '{}'.format(search_value)
        else:
            ons_env.logger.error('Environmental variable {} not set'.format(service_url_key))
            raise UploadException()

    @staticmethod
    def _send_message_to_rabbitmq(encrypted_message, tx_id):
        """
          Get details from environment credentials and send to rabbitmq
          :param encrypted_message: The encrypted message
          :param tx_id: The transaction id
          :return: Returns status code and message 
        """
        ons_env.logger.info('Getting environmental details for rabbit')
        rabbitmq_amqp = os.getenv('RABBITMQ_AMQP', ons_env.get('RABBITMQ_AMQP'))
        rabbit_mq = RabbitMQSubmitter(rabbitmq_amqp)

        if rabbit_mq.send_message(encrypted_message, QUEUE_NAME, tx_id):
            return 200, UPLOAD_SUCCESSFUL
        else:
            return 500, UPLOAD_UNSUCCESSFUL

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
    def _generate_file_name(ru, exercise_ref, survey_id, file_extension):
        """
        Generate the file name for the upload
        :param ru: reporting unit
        :param exercise_ref: exercise reference
        :param period: The collection period
        :param survey_id: The id of the survey
        :param file_extension: The upload file extension
        :return: file name
        """

        ons_env.logger.info('generating file name for upload')

        time_date_stamp = time.strftime("%d-%m-%Y-%H-%M-%S")
        time_date_stamp2 = time.strftime("%Y%m%d%H%M%S")
        file_name = "{ru}-{exercise_ref}-{time_date_stamp}{file_format}".format(ru=ru,
                                                                                exercise_ref=exercise_ref,
                                                                                survey_id=survey_id,
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
            raise UploadException()
        return response
