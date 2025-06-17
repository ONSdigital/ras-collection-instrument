import logging
from http import HTTPStatus

import structlog
from flask import Blueprint, jsonify, make_response, request
from werkzeug.exceptions import BadRequest

from application.controllers.basic_auth import auth
from application.controllers.registry_instrument import RegistryInstrument
from application.controllers.registry_instrument_validator import (
    validate_registry_instrument_payload,
)

log = structlog.wrap_logger(logging.getLogger(__name__))

registry_instrument_view = Blueprint("registry_instrument_view", __name__)


@registry_instrument_view.before_request
@auth.login_required
def before_registry_instrument_view():
    pass


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>", methods=["GET"])
def get_registry_instruments(exercise_id):
    """
    Returns an array of selected CIR instrument for the given collection exercise.

    :param exercise_id: An exercise id (UUID)
    """
    registry_instruments = RegistryInstrument().get_registry_instruments_by_exercise_id(exercise_id)

    # TODO: (low priority) check the exercise_id exists in the ras_ci.exercise table
    #       and return 404 if it does not exist

    return make_response(jsonify(registry_instruments), HTTPStatus.OK)


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
    :valid payload format example
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
        is_valid, error = validate_registry_instrument_payload(payload, exercise_id)
        if not is_valid:
            return make_response(error, HTTPStatus.BAD_REQUEST)
    except BadRequest:
        return make_response("Invalid JSON payload", HTTPStatus.BAD_REQUEST)

    survey_id = None
    instrument_id = None
    classifier_value = None
    ci_version = None
    guid = None
    published_at = None

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


@registry_instrument_view.route(
    "/registry-instrument/exercise-id/<exercise_id>/formtype/<form_type>", methods=["DELETE"]
)
def delete_registry_instrument(exercise_id, form_type):

    if RegistryInstrument().delete_registry_instrument_by_exercise_id_and_formtype(exercise_id, form_type):
        return make_response(
            "Successfully deleted registry instrument",
            HTTPStatus.OK,
        )
    else:
        return make_response("Not Found", HTTPStatus.NOT_FOUND)
