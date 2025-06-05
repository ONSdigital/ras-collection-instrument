import datetime
import logging
import re

import structlog
from flask import Blueprint, jsonify, make_response, request
from werkzeug.exceptions import BadRequest

from application.controllers.basic_auth import auth
from application.controllers.helper import validate_uuid
from application.controllers.registry_instrument import RegistryInstrument

log = structlog.wrap_logger(logging.getLogger(__name__))

registry_instrument_view = Blueprint("registry_instrument_view", __name__)


@registry_instrument_view.before_request
@auth.login_required
def before_registry_instrument_view():
    pass


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>", methods=["GET"])
def get_registry_instruments(exercise_id):
    registry_instruments = RegistryInstrument().get_registry_instruments_by_exercise_id(exercise_id)

    if registry_instruments:
        return make_response(jsonify(registry_instruments), 200)

    return make_response("Not Found", 404)


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>/formtype/<form_type>", methods=["GET"])
def get_registry_instrument(exercise_id, form_type):
    registry_instrument = RegistryInstrument().get_registry_instrument_by_exercise_id_and_formtype(
        exercise_id, form_type
    )

    if registry_instrument:
        return make_response(jsonify(registry_instrument), 200)

    return make_response("Not Found", 404)


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>", methods=["POST"])
def post_registry_instrument(exercise_id):
    """
    Create a selected CIR instrument for the given collection exercise

    :param exercise_id: An exercise id (UUID)
    :return: HTTP Status 201 if successful,
             400 if the payload is invalid,
             409 if a selected registry instrument already exists
    :payload format example
    {
        "ci_version": 1,
        "classifier_type": "form_type",
        "classifier_value": "0001",
        "exercise_id": "3ff59b73-7f15-406f-9e4d-7f00b41e85ce",
        "guid": "c046861a-0df7-443a-a963-d9aa3bddf328",
        "instrument_id": "dfc3ddd7-3e79-4c6b-a8f8-1fa184cdd06b",
        "published_at": "2025-12-31T00:00:00",
        "survey_id": "0b1f8376-28e9-4884-bea5-acf9d709464e"
    }
    """

    try:
        payload = request.get_json(force=True)
    except BadRequest:
        return make_response("Invalid JSON payload", 400)

    survey_id = None
    exercise_id = None
    instrument_id = None
    classifier_type = None
    classifier_value = None
    ci_version = None
    guid = None
    published_at = None

    if "classifier_type" in payload:
        classifier_type = payload["classifier_type"]
        if classifier_type not in ["form_type"]:
            return make_response("Invalid classifier type", 400)

    if "classifier_value" in payload:
        classifier_value = payload["classifier_value"]
        if not re.fullmatch(r"\d{4}", str(classifier_value)):
            return make_response("Invalid classifier value", 400)

    if "ci_version" in payload:
        ci_version = payload["ci_version"]
        try:
            ci_version = int(ci_version)
        except (ValueError, TypeError):
            return make_response("Invalid ci_version", 400)

    if "guid" in payload:
        guid = payload["guid"]
        if not validate_uuid(guid):
            return make_response("Invalid guid", 400)

    if "published_at" in payload:
        published_at = payload["published_at"]
        try:
            datetime.datetime.fromisoformat(published_at)
        except (ValueError, TypeError):
            return make_response("Invalid published_at", 400)

    if "survey_id" in payload:
        survey_id = payload["survey_id"]
        if not validate_uuid(survey_id):
            # TODO: check the survey_id exists in the ras_ci.survey table
            return make_response("Invalid survey_id", 400)

    if "instrument_id" in payload:
        instrument_id = payload["instrument_id"]
        if not validate_uuid(instrument_id):
            # TODO: check the instrument_id exists in the ras_ci.instrument table
            return make_response("Invalid instrument_id", 400)

    if "exercise_id" in payload:
        exercise_id = payload["exercise_id"]
        if not validate_uuid(exercise_id):
            # TODO: check the exercise_id exists in the ras_ci.exercise table
            return make_response("Invalid exercise_id", 400)

    registry_instrument = RegistryInstrument().get_registry_instrument_by_exercise_id_and_formtype(
        exercise_id, payload["classifier_value"]
    )

    if registry_instrument:
        return make_response("A selected registry instrument already exists for this exercise_id and form_type", 409)

    log.info(
        "The selected registry instrument would have been created, but the persistence layer is not implemented yet",
        survey_id=survey_id,
        exercise_id=exercise_id,
        instrument_id=instrument_id,
        classifier_type=classifier_type,
        classifier_value=classifier_value,
        ci_version=ci_version,
        published_at=published_at,
        guid=guid,
    )

    return make_response(
        "The selected registry instrument would have been created, but the persistence layer is not implemented yet",
        201,
    )
