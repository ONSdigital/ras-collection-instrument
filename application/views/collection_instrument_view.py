import logging

import structlog
from flask import Blueprint, current_app, jsonify, make_response, request

from application.controllers.basic_auth import auth
from application.controllers.collection_instrument import CollectionInstrument
from application.controllers.service_helper import collection_instrument_link, get_survey_ref
from application.exceptions import RasError
from application.models.google_cloud_bucket import GoogleCloudSEFTCIBucket

log = structlog.wrap_logger(logging.getLogger(__name__))

collection_instrument_view = Blueprint("collection_instrument_view", __name__)

COLLECTION_INSTRUMENT_NOT_FOUND = "Collection instrument not found"
NO_INSTRUMENT_FOR_EXERCISE = "There are no collection instruments for that exercise id"
UPLOAD_SUCCESSFUL = "The upload was successful"
PATCH_SUCCESSFUL = "The patch of the instrument was successful"
LINK_SUCCESSFUL = "Linked collection instrument to collection exercise"
UNLINK_SUCCESSFUL = "collection instrument and collection exercise unlinked"


@collection_instrument_view.before_request
@auth.login_required
def before_collection_instrument_view():
    pass


@collection_instrument_view.route("/upload/<exercise_id>", methods=["POST"])
@collection_instrument_view.route("/upload/<exercise_id>/<ru_ref>", methods=["POST"])
def upload_collection_instrument(exercise_id, ru_ref=None):
    file = request.files["file"]
    classifiers = request.args.get("classifiers")
    if current_app.config["SEFT_GCS_ENABLED"] is False:
        instrument = CollectionInstrument().upload_instrument(exercise_id, file, ru_ref=ru_ref, classifiers=classifiers)
    else:
        instrument = CollectionInstrument().upload_to_bucket(exercise_id, file, ru_ref=ru_ref, classifiers=classifiers)

    if not publish_uploaded_collection_instrument(exercise_id, instrument.instrument_id):
        log.error(
            "Failed to publish upload message",
            instrument_id=instrument.instrument_id,
            collection_exercise_id=exercise_id,
            ru_ref=ru_ref,
        )
        raise RasError("Failed to publish upload message", 500)
    return make_response(UPLOAD_SUCCESSFUL, 200)


@collection_instrument_view.route("/<instrument_id>", methods=["PATCH"])
def patch_collection_instrument(instrument_id):
    file = request.files["file"]
    if file.filename == "":
        raise RasError("Missing filename", 400)

    CollectionInstrument().patch_seft_instrument(instrument_id, file)

    return make_response(PATCH_SUCCESSFUL, 200)


@collection_instrument_view.route("/upload", methods=["POST"])
def upload_collection_instrument_without_collection_exercise():
    classifiers = request.args.get("classifiers")
    survey_id = request.args.get("survey_id")
    CollectionInstrument().upload_instrument_with_no_collection_exercise(survey_id, classifiers=classifiers)
    return make_response(UPLOAD_SUCCESSFUL, 200)


@collection_instrument_view.route("/link-exercise/<instrument_id>/<exercise_id>", methods=["POST"])
def link_collection_instrument(instrument_id, exercise_id):
    CollectionInstrument().link_instrument_to_exercise(instrument_id, exercise_id)
    response = publish_uploaded_collection_instrument(exercise_id, instrument_id)
    if response.status_code != 200:
        log.error("Failed to publish upload message", instrument_id=instrument_id, collection_exercise_id=exercise_id)
        raise RasError("Failed to publish upload message", 500)
    return make_response(LINK_SUCCESSFUL, 200)


@collection_instrument_view.route("/unlink-exercise/<instrument_id>/<exercise_id>", methods=["PUT"])
def unlink_collection_instrument(instrument_id, exercise_id):
    CollectionInstrument().unlink_instrument_from_exercise(instrument_id, exercise_id)
    return make_response(UNLINK_SUCCESSFUL, 200)


@collection_instrument_view.route("/download_csv/<exercise_id>", methods=["GET"])
def download_csv(exercise_id):
    csv = CollectionInstrument().get_instruments_by_exercise_id_csv(exercise_id)

    if csv:
        response = make_response(csv, 200)
        response.headers["Content-Disposition"] = "attachment; filename=instruments_for_{exercise_id}.csv".format(
            exercise_id=exercise_id
        )
        response.headers["Content-type"] = "text/csv"
        return response

    return make_response(NO_INSTRUMENT_FOR_EXERCISE, 404)


@collection_instrument_view.route("/migrate/<instrument_id>", methods=["GET"])
def migrate_collection_instrument(instrument_id):

    # Get the record out of the database
    collection_instrument = CollectionInstrument.get_instrument_json(instrument_id)
    exercises = collection_instrument['exercises']
    if len('exercises') == 0:
        return jsonify("No exercise associated with the SEFT", 400)
    if len(exercises) > 1:
        return jsonify("More than 1 exercise associated with the instrument", 400)
    if not collection_instrument['file_name']:
        return jsonify("Filename missing", 400)
    if not collection_instrument['file_name']:
        return jsonify("Filename missing", 400)

    exercise_id = exercises[0]

    survey_ref = get_survey_ref(collection_instrument['survey'])
    data = CollectionInstrument.get_instrument_data(instrument_id)
    filename = survey_ref + "/" + exercise_id + "/" + collection_instrument['file_name']
    # TODO sort out format of file so bucket uploader is happy
    # file.filename = filename
    seft_ci_bucket = GoogleCloudSEFTCIBucket(current_app.config)
    seft_ci_bucket.upload_file_to_bucket(file=data)

    # Decrypt data
    # Write it to the bucket under survey_ref/exercise_id/filename
    # Write the record back to the database with the data blanked and gcs set to true
    return '', 204



@collection_instrument_view.route("/collectioninstrument", methods=["GET"])
def collection_instrument_by_search_string():
    search_string = request.args.get("searchString")
    limit = request.args.get("limit")
    instruments = CollectionInstrument().get_instrument_by_search_string(search_string, limit)
    return make_response(jsonify(instruments), 200)


@collection_instrument_view.route("/collectioninstrument/count", methods=["GET"])
def count_collection_instruments_by_search_string():
    search_string = request.args.get("searchString")
    instruments = CollectionInstrument().get_instrument_by_search_string(search_string)
    return make_response(str(len(instruments)), 200)


@collection_instrument_view.route("/<instrument_id>", methods=["GET"])
@collection_instrument_view.route("/collectioninstrument/id/<instrument_id>", methods=["GET"])
def collection_instrument_by_id(instrument_id):
    # The /collectioninstrument/id/<id> endpoint needs to be removed once things that call it are replaced by
    # the simpler /<id> call above it
    instrument_json = CollectionInstrument().get_instrument_json(instrument_id)

    if instrument_json:
        return make_response(jsonify(instrument_json), 200)

    return make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)


@collection_instrument_view.route("/download/<instrument_id>", methods=["GET"])
def instrument_data(instrument_id):
    data, file_name = CollectionInstrument().get_instrument_data(instrument_id)

    if data and file_name:
        response = make_response(data, 200)
        response.headers["Content-Disposition"] = "attachment; filename={}".format(file_name)
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        response = make_response(COLLECTION_INSTRUMENT_NOT_FOUND, 404)

    return response


def publish_uploaded_collection_instrument(exercise_id, instrument_id):
    """
    Publish message to collection instrument link
    :param exercise_id: An exercise id (UUID)
    :param instrument_id: The id (UUID) for the newly created collection instrument
    :return True if message successfully linked
    """
    log.info("Publishing upload message", exercise_id=exercise_id, instrument_id=instrument_id)
    json_message = {"action": "ADD", "exercise_id": str(exercise_id), "instrument_id": str(instrument_id)}
    return collection_instrument_link(json_message)
