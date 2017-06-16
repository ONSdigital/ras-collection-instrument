from flask import jsonify, make_response


def session_scope_handler(error):
    return make_response(jsonify(error.message), error.status_code)