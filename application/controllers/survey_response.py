import logging
import time
import uuid

import structlog
from flask import current_app

from application.controllers.helper import (
    convert_file_object_to_string_base64,
    is_valid_file_extension,
    is_valid_file_name_length,
)
from application.controllers.service_helper import (
    get_business_party,
    get_case_group,
    get_collection_exercise,
    get_survey_ref,
)

log = structlog.wrap_logger(logging.getLogger(__name__))

UPLOAD_SUCCESSFUL = "Upload successful"
FILE_EXTENSION_ERROR = "The spreadsheet must be in .xls or .xlsx format"
FILE_NAME_LENGTH_ERROR = "The file name of your spreadsheet must be less than 50 characters long"
RABBIT_QUEUE_NAME = "Seft.Responses"


class FileTooSmallError(Exception):
    pass


class SurveyResponseError(Exception):
    pass


class SurveyResponse(object):

    """
    The survey response from a respondent
    """

    def add_survey_response(self, case_id, file_contents, file_name, survey_ref):
        """
        Encrypt and upload survey response to rabbitmq

        :param case_id: A case id
        :param file_contents: The contents of the file that has been uploaded
        :param file_name: The filename
        :param survey_ref: The survey ref e.g 134 MWSS
        :return: Returns boolean indicating success of upload of response to rabbitmq
        """

        tx_id = str(uuid.uuid4())
        bound_log = log.bind(filename=file_name, case_id=case_id, survey_id=survey_ref, tx_id=tx_id)
        bound_log.info("Adding survey response file")
        file_size = len(file_contents)

        if self.check_if_file_size_too_small(file_size):
            bound_log.info("File size is too small")
            raise FileTooSmallError()
        else:
            json_message = self._create_json_message_for_file(file_name, file_contents, case_id, survey_ref)
            sent = send_message_to_rabbitmq_queue(json_message, tx_id, RABBIT_QUEUE_NAME)
            if not sent:
                bound_log.error("Unable to send file to rabbit queue")
                raise SurveyResponseError()

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

        log.info("Creating json message", filename=file_name, case_id=case_id, survey_id=survey_ref)
        file_as_string = convert_file_object_to_string_base64(file)

        message_json = {"filename": file_name, "file": file_as_string, "case_id": case_id, "survey_id": survey_ref}

        return message_json

    @staticmethod
    def is_valid_file(file_name, file_extension):
        """
        Check a file is valid

        :param file_name: The file_name to check
        :param file_extension: The file extension
        :return: (boolean, String)
        """

        log.info("Checking if file is valid")
        if not is_valid_file_extension(file_extension, current_app.config.get("UPLOAD_FILE_EXTENSIONS")):
            log.info("File extension not valid", file_extension=file_extension)
            return False, FILE_EXTENSION_ERROR

        if not is_valid_file_name_length(file_name, current_app.config.get("MAX_UPLOAD_FILE_NAME_LENGTH")):
            log.info("File name too long", file_name=file_name)
            return False, FILE_NAME_LENGTH_ERROR

        return True, ""



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
            formatted_exercise_ref = exercise_ref.split("_")[1]
        except IndexError:
            formatted_exercise_ref = exercise_ref
        return formatted_exercise_ref
