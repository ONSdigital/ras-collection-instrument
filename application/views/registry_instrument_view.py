import datetime
import logging
import re
from http import HTTPStatus

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
        return make_response(jsonify(registry_instruments), HTTPStatus.OK)

    return make_response("Not Found", HTTPStatus.NOT_FOUND)


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>/formtype/<form_type>", methods=["GET"])
def get_registry_instrument(exercise_id, form_type):
    registry_instrument = RegistryInstrument().get_registry_instrument_by_exercise_id_and_formtype(
        exercise_id, form_type
    )

    if registry_instrument:
        return make_response(jsonify(registry_instrument), HTTPStatus.OK)

    return make_response("Not Found", HTTPStatus.NOT_FOUND)


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>", methods=["PUT"])
def put_registry_instrument(exercise_id):
    """
    Creates or updates a selected CIR instrument for the given collection exercise and form type.
    The exercise_id is a path parameter, and the form_type value is an attribute in the payload.
    We currently only support "classifier_type": "form_type" (e.g. where "classifier_value" is "0001").

    :param exercise_id: An exercise id (UUID)
    :payload format example
    {
        "survey_id": "0b1f8376-28e9-4884-bea5-acf9d709464e"
        "exercise_id": "3ff59b73-7f15-406f-9e4d-7f00b41e85ce",
        "instrument_id": "dfc3ddd7-3e79-4c6b-a8f8-1fa184cdd06b",
        "classifier_type": "form_type",
        "classifier_value": "0001",
        "ci_version": 1,
        "guid": "c046861a-0df7-443a-a963-d9aa3bddf328",
        "published_at": "2025-12-31T00:00:00",
    }
    :return: 201 if created successfully,
             200 if updated successfully,
             400 if the payload is invalid
    """

    try:
        payload = request.get_json(force=True)
    except BadRequest:
        return make_response("Invalid JSON payload", HTTPStatus.BAD_REQUEST)

    survey_id = None
    instrument_id = None
    classifier_value = None
    ci_version = None
    guid = None
    published_at = None

    # -------- Validate the payload --------

    # TODO: this will be all moved to an appropriate class once stable before PR is opened for review

    expected_keys = {
        "survey_id",
        "exercise_id",
        "instrument_id",
        "classifier_type",
        "classifier_value",
        "ci_version",
        "guid",
        "published_at",
    }

    payload_keys = set(payload.keys())

    if payload_keys != expected_keys:
        return make_response(f"Invalid payload keys. Expected: {expected_keys}", HTTPStatus.BAD_REQUEST)

    if "exercise_id" in payload:
        if payload["exercise_id"] != exercise_id:
            return make_response("exercise_id in payload does not match path parameter", HTTPStatus.BAD_REQUEST)
        if not validate_uuid(exercise_id):
            # TODO: check the exercise_id exists in the ras_ci.exercise table
            #       once the constraint is in place we could just rely on SQLAlchemy exception handling
            return make_response("Invalid exercise_id", HTTPStatus.BAD_REQUEST)

    if "survey_id" in payload:
        survey_id = payload["survey_id"]
        if not validate_uuid(survey_id):
            # TODO: check the survey_id exists in the ras_ci.survey table
            #       once the constraint is in place we could just rely on SQLAlchemy exception handling
            return make_response("Invalid survey_id", HTTPStatus.BAD_REQUEST)

    if "instrument_id" in payload:
        instrument_id = payload["instrument_id"]
        if not validate_uuid(instrument_id):
            # TODO: check the instrument_id exists in the ras_ci.instrument table
            #       once the constraint is in place we could just rely on SQLAlchemy exception handling
            return make_response("Invalid instrument_id", HTTPStatus.BAD_REQUEST)

    if "classifier_type" in payload:
        classifier_type = payload["classifier_type"]
        # currently we only support the "form_type" classifier
        if classifier_type not in ["form_type"]:
            return make_response("Invalid classifier type", HTTPStatus.BAD_REQUEST)

    if "classifier_value" in payload:
        classifier_value = payload["classifier_value"]
        if not re.fullmatch(r"\d{4}", str(classifier_value)):
            return make_response("Invalid classifier value", HTTPStatus.BAD_REQUEST)

    if "ci_version" in payload:
        ci_version = payload["ci_version"]
        try:
            ci_version = int(ci_version)
        except (ValueError, TypeError):
            return make_response("Invalid ci_version", HTTPStatus.BAD_REQUEST)

    if "guid" in payload:
        guid = payload["guid"]
        if not validate_uuid(guid):
            return make_response("Invalid guid", HTTPStatus.BAD_REQUEST)

    if "published_at" in payload:
        published_at = payload["published_at"]
        try:
            datetime.datetime.fromisoformat(published_at)
        except (ValueError, TypeError):
            return make_response("Invalid published_at", HTTPStatus.BAD_REQUEST)

    # -------- Completed validating the payload --------

    success, is_new = RegistryInstrument().save_registry_instrument_for_exercise_id_and_formtype(
        survey_id=survey_id,
        exercise_id=exercise_id,
        instrument_id=instrument_id,
        form_type=classifier_value,
        ci_version=ci_version,
        published_at=published_at,
        guid=guid,
    )

    if success:
        return make_response(
            "Successfully saved registry instrument",
            HTTPStatus.CREATED if is_new else HTTPStatus.OK,
        )
    else:
        return make_response(
            "Registry instrument failed to save successfully",
            HTTPStatus.INTERNAL_SERVER_ERROR,
        )
