import os
import time
import uuid

from application.controllers.helper import is_valid_file_extension, is_valid_file_name_length, \
    convert_file_object_to_string_base64
from application.controllers.json_encrypter import Encrypter
from application.controllers.rabbitmq_submitter import RabbitMQSubmitter
from application.controllers.service_request import service_request
from flask import current_app
from structlog import get_logger
from werkzeug.utils import secure_filename

log = get_logger()


FILE_EXTENSION_ERROR = 'The spreadsheet must be in .xls ot .xlsx format'
FILE_NAME_LENGTH_ERROR = 'The file name of your spreadsheet must be less than 50 characters long'
UPLOAD_SUCCESSFUL = 'Upload successful'
UPLOAD_UNSUCCESSFUL = 'Upload failed'
INVALID_UPLOAD = 'The upload must have valid case_id and a file attached'
NOT_FOUND_SERVICE_RESPONSE = 'A request to an external service returned no data'
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
        log.info('Adding survey response file {} for case {} with tx_id {}'.format(file, case_id, tx_id))

        if case_id and file and hasattr(file, 'filename'):
            file_name, file_extension = os.path.splitext(secure_filename(file.filename))
            is_valid_file, msg = self._is_valid_file(file_name, file_extension)

            if not is_valid_file:
                return 400, msg

            # request case_group from case service
            case = self._get_case(case_id)

            if not case or 'caseGroup' not in case:
                return self._not_found_service_response()

            case_group = case.get('caseGroup')
            ru = case_group.get('sampleUnitRef')
            collection_exercise_id = case_group.get('collectionExerciseId')

            # request collection_exercise from service
            collection_exercise = self._get_collection_exercise(collection_exercise_id)

            if collection_exercise:
                exercise_ref = collection_exercise.get('exerciseRef')
                formatted_exercise_ref = self._format_exercise_ref(exercise_ref)
                survey_id = collection_exercise.get('surveyId')
            else:
                return self._not_found_service_response()

            # request survey service data from survey service
            survey_ref = self._get_survey_ref(survey_id)

            if not survey_ref:
                return self._not_found_service_response()

            # Create, encrypt and send message to rabbitmq
            generated_file_name = self._generate_file_name(ru, formatted_exercise_ref, survey_ref, file_extension)
            file_contents = file.read()
            json_message = self._create_json_message_for_file(generated_file_name, file_contents, case_id)
            encrypted_message = self._encrypt_message(json_message)

            return self._send_message_to_rabbitmq(encrypted_message, tx_id)

        else:
            log.info('Case id or file missing')
            return 400, INVALID_UPLOAD

    @staticmethod
    def _create_json_message_for_file(generated_file_name, file, case_id):
        """
          Create json message from file
          :param generated_file_name: The generated file name
          :param file: The file uploaded
          :param case_id: The case UUID
          :return: Returns json message
        """

        log.info('Creating json message')
        file_as_string = convert_file_object_to_string_base64(file)

        message_json = {
            'filename': generated_file_name,
            'file': file_as_string,
            'case_id': case_id
        }

        return message_json

    @staticmethod
    def _get_case(case_id):
        """
        Get case details from service
        :param case_id: The case_id to search with
        :return: case details
        """

        case = None
        response = service_request(service='case-service', endpoint='cases', search_value=case_id)

        if response.status_code == 200:
            case = response.json()
        else:
            log.error("Case not found for {}".format(case_id))
        return case

    @staticmethod
    def _get_collection_exercise(collection_exercise_id):
        """
        Get collection exercise details from request
        :param collection_exercise_id: The collection_exercise_id to search with
        :return: collection_exercise
        """

        collection_exercise = None
        response = service_request(service='collectionexercise-service',
                                   endpoint='collectionexercises',
                                   search_value=collection_exercise_id)

        if response.status_code == 200:
            collection_exercise = response.json()
        else:
            log.info('Collection Exercise not found for {}'.format(collection_exercise_id))
        return collection_exercise

    @staticmethod
    def _get_survey_ref(survey_id):
        """
        :param survey_id: The survey_id UUID to search with
        :return: survey reference
        """

        survey_ref = None
        response = service_request(service='survey-service', endpoint='surveys', search_value=survey_id)

        if response.status_code == 200:
            survey_service_data = response.json()
            survey_ref = survey_service_data.get('surveyRef')
        else:
            log.debug('Survey service data not found')

        return survey_ref

    @staticmethod
    def _send_message_to_rabbitmq(encrypted_message, tx_id):
        """
          Get details from environment credentials and send to rabbitmq
          :param encrypted_message: The encrypted message
          :param tx_id: The transaction id
          :return: Returns status code and message
        """

        log.info('Getting environmental details for rabbit')
        rabbitmq_amqp = current_app.config.get('RABBITMQ_AMQP')
        rabbit_mq = RabbitMQSubmitter(rabbitmq_amqp)

        if rabbit_mq.send_message(encrypted_message, QUEUE_NAME, tx_id):
            log.info('Collection instrument successfully send to rabbitmq with tx_id {}'.format(tx_id))
            return 200, UPLOAD_SUCCESSFUL
        else:
            return 500, UPLOAD_UNSUCCESSFUL

    @staticmethod
    def _not_found_service_response():
        """
        Generic status code and message for when a request to an external service returns no data
        :return: status code, message
        """
        return 404, NOT_FOUND_SERVICE_RESPONSE

    @staticmethod
    def _is_valid_file(file_name, file_extension):
        """
        Check a file is valid
        :param file_name: The file_name to check
        :param file_extension: The file extension
        :return: boolean
        """

        log.info('Checking if file is valid')

        if not is_valid_file_extension(file_extension, current_app.config.get('UPLOAD_FILE_EXTENSIONS')):
            log.info('File extension not valid')
            return False, FILE_EXTENSION_ERROR

        if not is_valid_file_name_length(file_name, current_app.config.get('MAX_UPLOAD_FILE_NAME_LENGTH')):
            log.info('File name too long')
            return False, FILE_NAME_LENGTH_ERROR

        return True, ""

    @staticmethod
    def _encrypt_message(message_json):
        """
        encrypt the JSON message
        :param message_json: The file in json format
        :return: a jwe
        """

        log.info('Encrypting json')
        json_secret_keys = os.getenv('JSON_SECRET_KEYS')
        encrypter = Encrypter(json_secret_keys)
        return encrypter.encrypt(message_json)

    @staticmethod
    def _generate_file_name(ru, exercise_ref, survey_id, file_extension):
        """
        Generate the file name for the upload
        :param ru: reporting unit
        :param exercise_ref: exercise reference
        :param survey_id: The id of the survey
        :param file_extension: The upload file extension
        :return: file name
        """

        check_letter = 'X'  # Business related file name requirement
        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = "{ru}{check_letter}_{exercise_ref}_" \
                    "{survey_id}_{time_date_stamp}{file_format}".format(ru=ru,
                                                                        check_letter=check_letter,
                                                                        exercise_ref=exercise_ref,
                                                                        survey_id=survey_id,
                                                                        time_date_stamp=time_date_stamp,
                                                                        file_format=file_extension)

        log.info('Generated file name for upload. file name is: {}'.format(file_name))

        return file_name

    @staticmethod
    def _format_exercise_ref(exercise_ref):
        """
        There is currently data inconsistency in the code, exercise_ref should look like 201712 not '221_201712',
        this is a work around until the data is corrected
        :param exercise_ref: exercise reference
        :return: formatted exercise reference
        """
        try:
            formatted_exercise_ref = exercise_ref.split('_')[1]
        except IndexError:
            formatted_exercise_ref = exercise_ref
        return formatted_exercise_ref
