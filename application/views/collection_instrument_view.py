import logging
import structlog

from flask import Blueprint
from flask import make_response, request, jsonify

from application.controllers.basic_auth import auth
from application.controllers.collection_instrument import CollectionInstrument


log = structlog.wrap_logger(logging.getLogger(__name__))

collection_instrument_view = Blueprint('collection_instrument_view', __name__)

COLLECTION_INSTRUMENT_NOT_FOUND = 'Collection instrument not found'
NO_INSTRUMENT_FOR_EXERCISE = 'There are no collection instruments for that exercise id'
UPLOAD_SUCCESSFUL = 'The upload was successful'
LINK_SUCCESSFUL = 'Linked collection instrument to collection exercise'


@collection_instrument_view.before_request
@auth.login_required
def before_collection_instrument_view():
    pass


@collection_instrument_view.route('/upload/<exercise_id>', methods=['POST'])
@collection_instrument_view.route('/upload/<exercise_id>/<ru_ref>', methods=['POST'])
def upload_collection_instrument(exercise_id, ru_ref=None):
    file = request.files['file']
    classifiers = request.args.get('classifiers')
    CollectionInstrument().upload_instrument(exercise_id, file, ru_ref=ru_ref, classifiers=classifiers)
    return make_response(UPLOAD_SUCCESSFUL, 200)


@collection_instrument_view.route('/upload', methods=['POST'])
def upload_collection_instrument_without_collection_exercise():
    classifiers = request.args.get('classifiers')
    survey_id = request.args.get('survey_id')
    CollectionInstrument().upload_instrument_with_no_collection_exercise(survey_id, classifiers=classifiers)
    return make_response(UPLOAD_SUCCESSFUL, 200)


@collection_instrument_view.route('/link-exercise/<instrument_id>/<exercise_id>', methods=['POST'])
def link_collection_instrument(instrument_id, exercise_id):
    CollectionInstrument().link_instrument_to_exercise(instrument_id, exercise_id)
    return make_response(LINK_SUCCESSFUL, 200)


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


@collection_instrument_view.route('/collectioninstrument', methods=['GET'])
def collection_instrument_by_search_string():
    search_string = request.args.get('searchString')
    limit = request.args.get('limit')
    instruments = CollectionInstrument().get_instrument_by_search_string(search_string, limit)
    return make_response(jsonify(instruments), 200)


@collection_instrument_view.route('/collectioninstrument/count', methods=['GET'])
def count_collection_instruments_by_search_string():
    search_string = request.args.get('searchString')
    instruments = CollectionInstrument().get_instrument_by_search_string(search_string)
    return make_response(str(len(instruments)), 200)


@collection_instrument_view.route('/collectioninstrument/id/<instrument_id>', methods=['GET'])
def collection_instrument_by_id(instrument_id):
    instrument_json = CollectionInstrument().get_instrument_json(instrument_id)

    if instrument_json:
        return make_response(jsonify(instrument_json), 200)

    return make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)


@collection_instrument_view.route('/download/<instrument_id>', methods=['GET'])
def instrument_data(instrument_id):
    data, file_name = CollectionInstrument().get_instrument_data(instrument_id)

    if data and file_name:
        response = make_response(data, 200)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(file_name)
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        response = make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)

    return response


@collection_instrument_view.route('/instrument_size/<instrument_id>', methods=['GET'])
def instrument_size(instrument_id):
    instrument = CollectionInstrument().get_instrument_json(instrument_id)

    if instrument and 'len' in instrument:
        return make_response(str(instrument['len']), 200)

    return make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)
