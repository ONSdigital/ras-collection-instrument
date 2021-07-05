import logging
import os

import structlog
from flask import Blueprint, current_app, make_response, request
from werkzeug.utils import secure_filename

from application.controllers.basic_auth import auth
from application.controllers.gcp_survey_response import GcpSurveyResponse
from application.controllers.survey_response import FileTooSmallError, SurveyResponse, SurveyResponseError

log = structlog.wrap_logger(logging.getLogger(__name__))

survey_responses_view = Blueprint("survey_responses_view", __name__)
INVALID_UPLOAD = "The upload must have valid case_id and a file attached"
MISSING_DATA = "Data needed to create the file name is missing"
UPLOAD_SUCCESSFUL = "Upload successful"
UPLOAD_UNSUCCESSFUL = "Upload failed"
FILE_TOO_SMALL = "File too small"


@survey_responses_view.before_request
@auth.login_required
def before_survey_responses_view():
    pass


@survey_responses_view.route("/survey_responses/<case_id>", methods=["POST"])
def add_survey_response(case_id):

    file = request.files.get("file")

    if case_id and file and hasattr(file, "filename"):
        file_name, file_extension = os.path.splitext(secure_filename(file.filename))
        survey_response = SurveyResponse()
        is_valid_file, msg = survey_response.is_valid_file(file_name, file_extension)

        if not is_valid_file:
            return make_response(msg, 400)

        file_name, survey_ref = survey_response.get_file_name_and_survey_ref(case_id, file_extension)

        if not file_name:
            return make_response(MISSING_DATA, 404)
        try:
            file_contents = file.read()

            if current_app.config["SAVE_SEFT_IN_GCP"]:
                gcp_survey_response = GcpSurveyResponse(current_app.config)
                gcp_survey_response.add_survey_response(case_id, file_contents, file_name, survey_ref)
            else:
                survey_response.add_survey_response(case_id, file_contents, file_name, survey_ref)

            return make_response(UPLOAD_SUCCESSFUL, 200)
        except FileTooSmallError:
            return make_response(FILE_TOO_SMALL, 400)
        except SurveyResponseError:
            return make_response(UPLOAD_UNSUCCESSFUL, 500)

    else:
        return make_response(INVALID_UPLOAD, 400)
