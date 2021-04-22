import hashlib
import json
import logging
import sys
import time
import uuid

import structlog
from google.cloud import storage, pubsub_v1
from google.cloud.exceptions import GoogleCloudError

from application.controllers.helper import (is_valid_file_extension, is_valid_file_name_length,
                                            convert_file_object_to_string_base64)
from application.controllers.rabbit_helper import _encrypt_message
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


class GcpSurveyResponse:

    def __init__(self, config):
        self.config = config
        # Bucket config

        self.storage_client = None
        self.seft_bucket_name = self.config['SEFT_BUCKET_NAME']
        self.seft_bucket_file_prefix = self.config.get('SEFT_BUCKET_FILE_PREFIX')

        # Pubsub config
        self.publisher = None
        self.gcp_project_id = self.config['GOOGLE_CLOUD_PROJECT']
        self.seft_pubsub_topic = self.config['SEFT_PUBSUB_TOPIC']

    """
    The survey response from a respondent
    """
    def add_survey_response(self, case_id: str, file, file_name: str, survey_ref: str):
        """
        Encrypt and upload survey response to gcp

        :param case_id: A case id
        :param file: A file object from which we can read the file contents
        :param file_name: The filename
        :param survey_ref: The survey ref e.g 134 MWSS
        :return: Returns boolean indicating success of upload of response to rabbitmq
        """

        tx_id = str(uuid.uuid4())
        bound_log = log.bind(filename=file_name, case_id=case_id, survey_id=survey_ref, tx_id=tx_id)
        bound_log.info('Putting response into bucket and sending pubsub message')
        file_size = len(file)

        if self.check_if_file_size_too_small(file_size):
            bound_log.info('File size is too small')
            raise FileTooSmallError()
        else:
            json_message = self._create_json_message_for_file(file_name, file, case_id, survey_ref)
            try:
                payload = self.create_pubsub_payload(json_message, tx_id)
            except SurveyResponseError:
                bound_log.error("Something went wrong creating the payload", exc_info=True)
                raise

            try:
                self.put_file_into_gcp_bucket(json_message)
            except (GoogleCloudError, KeyError):
                bound_log.exception("Something went wrong putting into the bucket")
                raise SurveyResponseError()

            try:
                self.put_message_into_pubsub(payload)
            except TimeoutError:
                bound_log.exception("Publish to pubsub timed out", payload=payload)
                raise SurveyResponseError()
            except Exception as e:  # noqa
                bound_log.exception("A non-timeout error was raised when publishing to pubsub", payload=payload)
                raise SurveyResponseError()

    def put_file_into_gcp_bucket(self, message):
        """
        Takes the message (containing the file) and puts it into a GCP bucket to be later used by SDX.

        Note: The payload will almost certainly change once the encryption method between us and SDX is decided, but
        for now we'll put the same payload we were using in rabbit as a starting point.

        :param message: A dict with metadata about the collection instrument
        :type message: dict
        """
        bound_log = log.bind(project=self.gcp_project_id, bucket=self.seft_bucket_name)
        bound_log.info('Starting to put file in bucket')
        if self.storage_client is None:
            self.storage_client = storage.Client(project=self.gcp_project_id)

        bucket = self.storage_client.bucket(self.seft_bucket_name)
        try:
            if self.seft_bucket_file_prefix:
                filename = f"{self.seft_bucket_file_prefix}/{message['filename']}"
            else:
                filename = message['filename']
            blob = bucket.blob(filename)
        except KeyError:
            bound_log.info('Missing filename from the message', message=message)
            raise
        encrypted_message = _encrypt_message(message)
        blob.upload_from_string(encrypted_message)
        bound_log.info('Successfully put file in bucket', filename=filename)

    def put_message_into_pubsub(self, payload):
        """
        Takes some metadata about the collection instrument and puts a message on pubsub for SDX to consume.

        :param payload: The payload to be put onto the pubsub topic
        :type payload: dict
        """
        if self.publisher is None:
            self.publisher = pubsub_v1.PublisherClient()

        topic_path = self.publisher.topic_path(self.gcp_project_id, self.seft_pubsub_topic) # NOQA pylint:disable=no-member
        payload_bytes = json.dumps(payload).encode()
        log.info("About to publish to pubsub", topic_path=topic_path)
        future = self.publisher.publish(topic_path, data=payload_bytes)
        message = future.result(timeout=15)
        log.info("Publish succeeded", msg_id=message)

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

    def create_pubsub_payload(self, message, tx_id) -> dict:
        case_id = message['case_id']
        log.info('Creating pubsub payload', case_id=case_id)

        case_group = get_case_group(case_id)
        if not case_group:
            raise SurveyResponseError()

        collection_exercise_id = case_group.get('collectionExerciseId')
        collection_exercise = get_collection_exercise(collection_exercise_id)
        if not collection_exercise:
            raise SurveyResponseError("Collection exercise not found")

        exercise_ref = collection_exercise.get('exerciseRef')
        survey_id = collection_exercise.get('surveyId')
        survey_ref = get_survey_ref(survey_id)
        if not survey_ref:
            raise SurveyResponseError("Survey ref not found")

        ru = case_group.get('sampleUnitRef')
        exercise_ref = self._format_exercise_ref(exercise_ref)

        business_party = get_business_party(case_group['partyId'],
                                            collection_exercise_id=collection_exercise_id, verbose=True)
        if not business_party:
            raise SurveyResponseError("Business not found in party")
        check_letter = business_party['checkletter']
        time_date_stamp = time.strftime("%Y%m%d%H%M%S")
        file_name = f"{ru}{check_letter}_{exercise_ref}_{survey_ref}_{time_date_stamp}"

        # We'll probably need to change how we get the md5 and sizeBytes when the interface with SDX is more
        # clearly defined.
        payload = {
            "filename": file_name,
            "tx_id": tx_id,
            "survey_id": survey_ref,
            "period": exercise_ref,
            "ru_ref": ru,
            "md5sum": hashlib.md5(message),
            "sizeBytes": sys.getsizeof(message)
        }
        log.info("Payload created", payload=payload)

        return payload

    @staticmethod
    def check_if_file_size_too_small(file_size) -> bool:
        return file_size < 1

    @staticmethod
    def _format_exercise_ref(exercise_ref: str) -> str:
        """
        There is currently data inconsistency in the code, exercise_ref should look like 201712 not '221_201712',
        this is a work around until the data is corrected

        :param exercise_ref: exercise reference
        :return: formatted exercise reference
        """
        try:
            return exercise_ref.split('_')[1]
        except IndexError:
            return exercise_ref
