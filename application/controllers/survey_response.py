import os
import time
import uuid

from flask import current_app
from sdc.rabbit.exceptions import PublishMessageError
from sdc.rabbit.publisher import QueuePublisher
from structlog import get_logger

from application.controllers.helper import (is_valid_file_extension, is_valid_file_name_length,
                                            convert_file_object_to_string_base64)
from application.controllers.json_encrypter import Encrypter
from application.controllers.service_helper import get_case_group, get_collection_exercise, get_survey_ref


log = get_logger()

FILE_EXTENSION_ERROR = 'The spreadsheet must be in .xls or .xlsx format'
FILE_NAME_LENGTH_ERROR = 'The file name of your spreadsheet must be less than 50 characters long'
QUEUE_NAME = 'Seft.Responses'


class SurveyResponse(object):
    """
    The survey response from a respondent
    """
    def add_survey_response(self, case_id, file, file_name, survey_ref):
        """
        Encrypt and upload survey response to rabbitmq
        :param case_id: A case id
        :param file: A file object from which we can read the file contents
        :param file_name: The filename
        :param survey_ref: The survey ref e.g 134 MWSS
        :return: Returns boolean
        """

        tx_id = str(uuid.uuid4())
        log.info('Adding survey response file {} for case {} survey {} with tx_id {}'.format(file, case_id,
                                                                                             survey_ref, tx_id))

        file_contents = file.read()
        json_message = self._create_json_message_for_file(file_name, file_contents, case_id, survey_ref)
        encrypted_message = self._encrypt_message(json_message)
        return self._send_message_to_rabbitmq(encrypted_message, tx_id)

    @staticmethod
    def _create_json_message_for_file(generated_file_name, file, case_id, survey_ref):
        """
          Create json message from file
          :param generated_file_name: The generated file name
          :param file: The file uploaded
          :param case_id: The case UUID
          :param survey_ref : The survey reference e.g 134 MWSS
          :return: Returns json message
          ..note:: the confusing use of survey_id and survey ref . collection_exercise returns uses survey_id as a
          guid which is the guid as defined in the survey_service . The survey service holds a survey_ref
          which is a 3 character string holding defining an integer which other (older) services refer to as survey_id
          therefore when passing to sdx we use the survey_ref not the survey_id in the survey_id field of the json.
        """

        log.info('Creating json message filename:{0} case_id:{1} survey_id:{2}'.format(generated_file_name, case_id,
                                                                                       survey_ref))
        file_as_string = convert_file_object_to_string_base64(file)

        message_json = {
            'filename': generated_file_name,
            'file': file_as_string,
            'case_id': case_id,
            'survey_id': survey_ref
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
        publisher = QueuePublisher([rabbitmq_amqp], QUEUE_NAME)
        try:
            publisher.publish_message(encrypted_message, headers={"tx_id": tx_id},
                                      immediate=False, mandatory=True)
            log.info('Collection instrument successfully send to rabbitmq with tx_id {}'
                     .format(tx_id))
            return True
        except PublishMessageError:
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

    def get_file_name_and_survey_ref(self, case_id, file_extension):
        """
        Generate the file name for the upload, if an external service can't find the relevant information
        a None is returned instead.
        :param case_id: The case id of the upload
        :param file_extension: The upload file extension
        :return: file name and survey_ref or None
        ..note:: returns two seemingly disparate values because the survey_ref is needed for filename anyway,
            and resolving requires calls to http services, doing it in one function minimises network traffic.
            survey_id as returned by collection exercise is a uuid, this is resolved by a call to
            survey which returns it as surveyRef which is the 3 digit id that other services refer to as survey_id
        """

        log.info('Generating file name for {case_id}'.format(case_id=case_id))

        case_group = get_case_group(case_id)
        if not case_group:
            return None, None

        collection_exercise_id = case_group.get('collectionExerciseId')
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            return None, None

        exercise_ref = collection_exercise.get('exerciseRef')
        survey_id = collection_exercise.get('surveyId')
        survey_ref = get_survey_ref(survey_id)
        if not survey_ref:
            return None, None

        ru = case_group.get('sampleUnitRef')
        exercise_ref = self._format_exercise_ref(exercise_ref)

        check_letter = 'X'  # Business related file name requirement
        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = "{ru}{check_letter}_{exercise_ref}_" \
                    "{survey_ref}_{time_date_stamp}{file_format}".format(ru=ru,
                                                                         check_letter=check_letter,
                                                                         exercise_ref=exercise_ref,
                                                                         survey_ref=survey_ref,
                                                                         time_date_stamp=time_date_stamp,
                                                                         file_format=file_extension)

        log.info('Generated file name for upload. file name is: {}'.format(file_name))

        return file_name, survey_ref

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
