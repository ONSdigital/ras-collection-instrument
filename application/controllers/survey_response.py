import os
import time
import uuid

from application.controllers.helper import is_valid_file_extension, is_valid_file_name_length, \
    convert_file_object_to_string_base64
from application.controllers.json_encrypter import Encrypter
from application.controllers.rabbitmq_submitter import RabbitMQSubmitter
from flask import current_app
from structlog import get_logger
from application.controllers.service_helper import get_case_group, get_collection_exercise, get_survey_ref

log = get_logger()

FILE_EXTENSION_ERROR = 'The spreadsheet must be in .xls or .xlsx format'
FILE_NAME_LENGTH_ERROR = 'The file name of your spreadsheet must be less than 50 characters long'
QUEUE_NAME = 'Seft.Responses'


class SurveyResponse(object):
    """
    The survey response from a respondent
    """
    def add_survey_response(self, case_id, file, file_name):
        """
        Encrypt and upload survey response to rabbitmq
        :param case_id: A case id
        :param file: A file object from which we can read the file contents
        :param file_name: The filename
        :return: Returns boolean
        """

        tx_id = str(uuid.uuid4())
        log.info('Adding survey response file {} for case {} with tx_id {}'.format(file, case_id, tx_id))

        file_contents = file.read()
        json_message = self._create_json_message_for_file(file_name, file_contents, case_id)
        encrypted_message = self._encrypt_message(json_message)
        return self._send_message_to_rabbitmq(encrypted_message, tx_id)

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
            return True
        else:
            return False

    @staticmethod
    def is_valid_file(file_name, file_extension):
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

    def generate_file_name(self, case_id, file_extension):
        """
        Generate the file name for the upload, if an external service can't find the relevant information
        a None is returned instead.
        :param case_id: The case id of the upload
        :param file_extension: The upload file extension
        :return: file name or None
        """

        log.info('Generating file name for {case_id}'.format(case_id=case_id))

        case_group = get_case_group(case_id)
        if not case_group:
            return None

        collection_exercise_id = case_group.get('collectionExerciseId')
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if collection_exercise:
            exercise_ref = collection_exercise.get('exerciseRef')
            survey_id = collection_exercise.get('surveyId')
        else:
            return None

        survey_ref = get_survey_ref(survey_id)
        if not survey_ref:
            return None

        ru = case_group.get('sampleUnitRef')
        exercise_ref = self._format_exercise_ref(exercise_ref)

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
