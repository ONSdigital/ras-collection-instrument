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
