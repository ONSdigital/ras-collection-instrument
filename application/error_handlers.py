import logging

from structlog import wrap_logger
from ras_common_utils.ras_error.ras_error import RasError
from flask import jsonify
from application import app

logger = wrap_logger(logging.getLogger(__name__))


@app.errorhandler(Exception)
def handle_error(error):
    if isinstance(error, RasError):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
    else:
        response = jsonify({'errors': [str(error)]})
        response.status_code = 500
    return response
