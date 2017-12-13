import logging
import structlog

from application.exceptions import RasError
from flask import jsonify
from application import app

log = structlog.wrap_logger(logging.getLogger(__name__))


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, RasError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
    else:
        response = jsonify({'errors': [str(error)]})
        response.status_code = 500
    return response
