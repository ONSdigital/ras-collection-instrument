from flask import Blueprint, make_response, current_app, jsonify

info_view = Blueprint('info_view', __name__)


@info_view.route('/info', methods=['GET'])
def get_info():
    return make_response(
        jsonify({
            "name": current_app.config['NAME'],
            "version": current_app.config['VERSION'],
        }), 200)
