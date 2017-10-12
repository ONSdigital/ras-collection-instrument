from application.controllers.basic_auth import auth
from application.controllers.survey_response import SurveyResponse
from flask import Blueprint
from flask import make_response, request
from structlog import get_logger

log = get_logger()

survey_responses_view = Blueprint('survey_responses_view', __name__)


@auth.login_required
@survey_responses_view.route('/survey_responses/<case_id>', methods=['POST'])
def survey_response(case_id):
    file = request.files['file']
    code, msg = SurveyResponse().add_survey_response(case_id, file)
    return make_response(msg, code)
