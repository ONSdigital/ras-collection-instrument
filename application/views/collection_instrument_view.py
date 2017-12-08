from application.controllers.basic_auth import auth
from application.controllers.collection_instrument import CollectionInstrument
from flask import Blueprint
from flask import make_response, request, jsonify
from structlog import get_logger

log = get_logger()

collection_instrument_view = Blueprint('collection_instrument_view', __name__)

COLLECTION_INSTRUMENT_NOT_FOUND = 'Collection instrument not found'
NO_INSTRUMENT_FOR_EXERCISE = 'There are no collection instruments for that exercise id'


@auth.login_required
@collection_instrument_view.route('/upload/<exercise_id>/<ru_ref>', methods=['POST'])
def upload_collection_instrument(exercise_id, ru_ref):
    file = request.files['file']
    msg = CollectionInstrument().upload_instrument(exercise_id, ru_ref, file)
    return make_response(msg, 200)


@auth.login_required
@collection_instrument_view.route('/download_csv/<exercise_id>', methods=['GET'])
def download_csv(exercise_id):
    csv = CollectionInstrument().get_instruments_by_exercise_id_csv(exercise_id)

    if csv:
        response = make_response(csv, 200)
        response.headers["Content-Disposition"] = "attachment; filename=instruments_for_{exercise_id}.csv"\
                .format(exercise_id=exercise_id)
        response.headers["Content-type"] = "text/csv"
        return response

    return make_response(NO_INSTRUMENT_FOR_EXERCISE, 404)


@auth.login_required
@collection_instrument_view.route('/collectioninstrument', methods=['GET'])
def collection_instrument_by_search_string():
    search_string = request.args.get('searchString')
    instruments = CollectionInstrument().get_instrument_by_search_string(search_string)
    return make_response(jsonify(instruments), 200)


@auth.login_required
@collection_instrument_view.route('/collectioninstrument/id/<instrument_id>', methods=['GET'])
def collection_instrument_by_id(instrument_id):
    instrument_json = CollectionInstrument().get_instrument_json(instrument_id)

    if instrument_json:
        return make_response(jsonify(instrument_json), 200)

    return make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)


@auth.login_required
@collection_instrument_view.route('/download/<instrument_id>', methods=['GET'])
def instrument_data(instrument_id):
    data, ru_ref = CollectionInstrument().get_instrument_data(instrument_id)

    if data and ru_ref:
        response = make_response(data, 200)
        response.headers["Content-Disposition"] = "attachment; filename={}.xlsx".format(ru_ref)
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        response = make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)

    return response


@auth.login_required
@collection_instrument_view.route('/instrument_size/<instrument_id>', methods=['GET'])
def instrument_size(instrument_id):
    instrument = CollectionInstrument().get_instrument_json(instrument_id)

    if instrument and 'len' in instrument:
        return make_response(jsonify(instrument['len']), 200)

    return make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)
