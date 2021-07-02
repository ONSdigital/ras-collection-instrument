import logging

import structlog
from flask import Blueprint, jsonify

from application.exceptions import RasError

log = structlog.wrap_logger(logging.getLogger(__name__))

error_blueprint = Blueprint("error_handlers", __name__)


@error_blueprint.app_errorhandler(Exception)
def handle_error(error):
    log.exception("An generic exception was raised")
    if isinstance(error, RasError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
    else:
        response = jsonify({"errors": [str(error)]})
        response.status_code = 500
    return response
