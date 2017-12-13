from application.controllers.basic_auth import auth
from application.controllers.survey_response import SurveyResponse
from flask import Blueprint
from flask import make_response, request
from structlog import get_logger
import os
from werkzeug.utils import secure_filename

log = get_logger()

survey_responses_view = Blueprint('survey_responses_view', __name__)
INVALID_UPLOAD = 'The upload must have valid case_id and a file attached'
MISSING_DATA = 'Data needed to create the file name is missing'
UPLOAD_SUCCESSFUL = 'Upload successful'
UPLOAD_UNSUCCESSFUL = 'Upload failed'


@auth.login_required
@survey_responses_view.route('/survey_responses/<case_id>', methods=['POST'])
def add_survey_response(case_id):

    file = request.files.get('file')

    if case_id and file and hasattr(file, 'filename'):
        file_name, file_extension = os.path.splitext(secure_filename(file.filename))
        survey_response = SurveyResponse()
        is_valid_file, msg = survey_response.is_valid_file(file_name, file_extension)

        if not is_valid_file:
            return make_response(msg, 400)

        file_name, survey_ref = survey_response.get_file_name_and_survey_ref(case_id, file_extension)

        if not file_name:
            return make_response(MISSING_DATA, 404)

        upload_success = survey_response.add_survey_response(case_id, file, file_name, survey_ref)

        if upload_success:
            return make_response(UPLOAD_SUCCESSFUL, 200)
        else:
            return make_response(UPLOAD_UNSUCCESSFUL, 500)

    else:
        return make_response(INVALID_UPLOAD, 400)