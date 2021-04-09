import hashlib
import logging
import sys
import time
import uuid

import structlog
from flask import current_app
from google.cloud import storage, pubsub_v1
from google.cloud.exceptions import GoogleCloudError

from application.controllers.helper import (is_valid_file_extension, is_valid_file_name_length,
                                            convert_file_object_to_string_base64)
from application.controllers.rabbit_helper import initialise_rabbitmq_queue, send_message_to_rabbitmq_queue, \
    _encrypt_message
from application.controllers.service_helper import (get_business_party, get_case_group, get_collection_exercise,
                                                    get_survey_ref)
log = structlog.wrap_logger(logging.getLogger(__name__))

UPLOAD_SUCCESSFUL = 'Upload successful'
FILE_EXTENSION_ERROR = 'The spreadsheet must be in .xls or .xlsx format'
FILE_NAME_LENGTH_ERROR = 'The file name of your spreadsheet must be less than 50 characters long'
RABBIT_QUEUE_NAME = 'Seft.Responses'


class FileTooSmallError(Exception):
    pass


class SurveyResponseError(Exception):
    pass


class GcpSurveyResponse(object):

    def __init__(self):
        self.storage_client = None
        self.publisher = None
        self.seft_bucket_name = None
        self.gcp_project_id = None
        self.seft_pubsub_topic = None

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
        :return: Returns boolean indicating success of upload of response to rabbitmq
        """

        tx_id = str(uuid.uuid4())
        bound_log = log.bind(filename=file_name, case_id=case_id, survey_id=survey_ref, tx_id=tx_id)
        bound_log.info('Adding survey response file')
        file_contents = file.read()
        file_size = len(file_contents)

        if self.check_if_file_size_too_small(file_size):
            bound_log.info('File size is too small')
            raise FileTooSmallError()
        else:
            json_message = self._create_json_message_for_file(file_name, file_contents, case_id, survey_ref)

            if current_app.config['SAVE_SEFT_IN_GCP']:
                try:
                    self.put_file_into_gcp_bucket(json_message)
                except GoogleCloudError:
                    bound_log.error("Something went wrong putting into the bucket")

                try:
                    self.put_message_into_pubsub(json_message)
                except TimeoutError:
                    bound_log.error("Publish to pubsub timed out", exc_info=True)
                    # Delete previously added file from bucket
                    raise SurveyResponseError()
                except Exception:  # noqa
                    bound_log.error("A non-timeout error was raised when publishing to pubsub", exc_info=True)
                    # Delete previously added from bucket
                    raise SurveyResponseError()

    def put_file_into_gcp_bucket(self, message):
        """
        Takes the message (containing the file) and puts it into a GCP bucket to be later used by SDX.

        Note: The payload will almost certainly change once the encryption method between us and SDX is decided, but
        for now we'll put the same payload we were using in rabbit as a starting point.

        :param message: A dict with metadata about the collection instrument
        :type message: dict
        """
        if self.storage_client is None:
            self.storage_client = storage.Client()

        bucket = self.storage_client.get_bucket(self.seft_bucket_name)
        try:
            blob = bucket.blob(message['filename'])
        except KeyError:
            log.info('Missing filename from the message', message=message)
            raise
        encrypted_message = _encrypt_message(message)
        blob.upload_from_string(encrypted_message)

    def put_message_into_pubsub(self, message):
        """
        Takes some metadata about the collection instrument and puts a message on pubsub for SDX to consume.

        :param message: A dict with metadata about the collection instrument
        :type message: dict
        """
        if self.publisher is None:
            self.publisher = pubsub_v1.PublisherClient()

        topic_path = self.publisher.topic_path(self.gcp_project_id, self.seft_pubsub_topic) # NOQA pylint:disable=no-member
        payload = self.create_pubsub_payload(message)

        log.info("About to publish to pubsub")
        future = self.publisher.publish(topic_path, data=payload)
        message = future.result(timeout=15)
        log.info("Publish succeeded", msg_id=message)

    @staticmethod
    def initialise_messaging():
        log.info('Initialising rabbitmq queue for Survey Responses', queue=RABBIT_QUEUE_NAME)
        return initialise_rabbitmq_queue(RABBIT_QUEUE_NAME)

    @staticmethod
    def _create_json_message_for_file(file_name, file, case_id, survey_ref):
        """
        Create json message from file

        .. note:: the confusing use of survey_id and survey_ref. collection_exercise returns uses survey_id as a
            GUID, which is the GUID as defined in the survey_service. The survey service holds a survey_ref,
            a 3 character string holding defining an integer, which other (older) services refer to as survey_id.
            Therefore, when passing to sdx we use the survey_ref not the survey_id in the survey_id field of the json.

        :param file_name: The file name
        :param file: The file uploaded
        :param case_id: The case UUID
        :param survey_ref : The survey reference e.g 134 MWSS
        :return: Returns json message
        """

        log.info('Creating json message', filename=file_name, case_id=case_id, survey_id=survey_ref)
        file_as_string = convert_file_object_to_string_base64(file)

        message_json = {
            'filename': file_name,
            'file': file_as_string,
            'case_id': case_id,
            'survey_id': survey_ref
        }

        return message_json

    @staticmethod
    def is_valid_file(file_name, file_extension):
        """
        Check a file is valid

        :param file_name: The file_name to check
        :param file_extension: The file extension
        :return: (boolean, String)
        """

        log.info('Checking if file is valid')
        if not is_valid_file_extension(file_extension, current_app.config.get('UPLOAD_FILE_EXTENSIONS')):
            log.info('File extension not valid')
            return False, FILE_EXTENSION_ERROR

        if not is_valid_file_name_length(file_name, current_app.config.get('MAX_UPLOAD_FILE_NAME_LENGTH')):
            log.info('File name too long')
            return False, FILE_NAME_LENGTH_ERROR

        return True, ""

    def create_pubsub_payload(self, message):

        case_id = message['case_id']
        log.info('Generating file name', case_id=case_id)

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
            return None

        ru = case_group.get('sampleUnitRef')
        exercise_ref = self._format_exercise_ref(exercise_ref)

        business_party = get_business_party(case_group['partyId'],
                                            collection_exercise_id=collection_exercise_id, verbose=True)
        if not business_party:
            return None
        check_letter = business_party['checkletter']
        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = f"{ru}{check_letter}_{exercise_ref}_{survey_ref}_{time_date_stamp}"

        # We'll probably need to change how we get the md5 and sizeBytes when the interface with SDX is more
        # clearly defined.  We might need to write to the bucket, then read it back to find out
        # how big GCP thinks it is?
        payload = {
            "filename": file_name,
            "tx_id": message['tx_id'],
            "survey_id": survey_ref,
            "period": exercise_ref,
            "ru_ref": ru,
            "md5sum": hashlib.md5(message),
            "sizeBytes": sys.getsizeof(message)
        }

        return payload

    @staticmethod
    def check_if_file_size_too_small(file_size):
        return file_size < 1

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
