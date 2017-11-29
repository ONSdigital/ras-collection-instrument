from application.controllers.basic_auth import auth
from application.controllers.collection_instrument import CollectionInstrument
from flask import Blueprint
from flask import make_response, request, jsonify
from structlog import get_logger

log = get_logger()

collection_instrument_view = Blueprint('collection_instrument_view', __name__)


@auth.login_required
@collection_instrument_view.route('/upload/<exercise_id>/<ru_ref>', methods=['POST'])
def upload_collection_instrument(exercise_id, ru_ref):
    file = request.files['file']
    code, msg = CollectionInstrument().upload_instrument(exercise_id, ru_ref, file)
    return make_response(msg, code)


@auth.login_required
@collection_instrument_view.route('/download_csv/<exercise_id>', methods=['GET'])
def download_csv(exercise_id):
    code, msg = CollectionInstrument().get_instruments_by_exercise_id_csv(exercise_id)
    response = make_response(msg, code)

    if code == 200:
        response.headers["Content-Disposition"] = "attachment; filename=instruments_for_{exercise_id}.csv"\
                .format(exercise_id=exercise_id)
        response.headers["Content-type"] = "text/csv"
    return response


@auth.login_required
@collection_instrument_view.route('/collectioninstrument', methods=['GET'])
def collection_instrument_by_search_string():
    search_string = request.args.get('searchString')
    code, msg = CollectionInstrument().get_instrument_by_search_string(search_string)
    return make_response(jsonify(msg), code)


@auth.login_required
@collection_instrument_view.route('/collectioninstrument/id/<instrument_id>', methods=['GET'])
def collection_instrument_by_id(instrument_id):
    code, msg = CollectionInstrument().get_instrument_by_id(instrument_id)
    return make_response(jsonify(msg), code)
