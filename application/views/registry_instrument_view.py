import logging

import structlog
from flask import Blueprint, jsonify, make_response

from application.controllers.basic_auth import auth
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

    # stubbing the above until I map the returned model to the json
    stubbed_registry_instruments = {
        "registry_instruments": [
            {
                "exercise_id": exercise_id,
                "instrument_id": "dfc3ddd7-3e79-4c6b-a8f8-1fa184cdd06b",
                "survey_id": "0b1f8376-28e9-4884-bea5-acf9d709464e",
                "classifier_type": "form_type",
                "classifier_value": "0001",
                "ci_version": 1,
                "guid": "c046861a-0df7-443a-a963-d9aa3bddf328",
                "published_at": "2025-12-31T00:00:00",
            },
            {
                "exercise_id": exercise_id,
                "instrument_id": "77c1e406-716a-488d-bfc9-b5b988fbaccf",
                "survey_id": "0b1f8376-28e9-4884-bea5-acf9d709464e",
                "classifier_type": "form_type",
                "classifier_value": "0002",
                "ci_version": 3,
                "guid": "ac3c5a3a-2ebb-47dc-9727-22c473086a82",
                "published_at": "2025-12-31T12:00:00",
            },
        ]
    }

    if registry_instruments:
        return make_response(jsonify(stubbed_registry_instruments), 200)

    return make_response("Not Found", 404)


@registry_instrument_view.route("/registry-instrument/exercise-id/<exercise_id>/formtype/<form_type>", methods=["GET"])
def get_registry_instrument(exercise_id, form_type):
    registry_instrument = RegistryInstrument().get_registry_instrument_by_exercise_id_and_formtype(
        exercise_id, form_type
    )

    # stubbing the above until I map the returned model to the json
    stubbed_registry_instrument = {
            "exercise_id": exercise_id,
            "instrument_id": "dfc3ddd7-3e79-4c6b-a8f8-1fa184cdd06b",
            "survey_id": "0b1f8376-28e9-4884-bea5-acf9d709464e",
            "classifier_type": "form_type",
            "classifier_value": form_type,
            "ci_version": 1,
            "guid": "c046861a-0df7-443a-a963-d9aa3bddf328",
            "published_at": "2025-12-31T00:00:00",
        }

    if registry_instrument:
        return make_response(jsonify(stubbed_registry_instrument), 200)

    return make_response("Not Found", 404)
