##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from uuid import uuid4
from flask import request, jsonify, make_response
from structlog import get_logger
from .collectioninstrument import CollectionInstrument
from .ons_jwt import validate_jwt
from .controller_helper import ensure_log_on_error, bind_request_detail_to_log

collection_instrument = CollectionInstrument()
logger = get_logger()


#
# /status/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def status_id_get(id):
    """
    Get upload status
    Return a count of items thus far and total in batch
    :param id: Survey identifier
    :type id: str

    :rtype: None
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.status(id)
    ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)


#
# /define_batch/{id}/{count}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def define_batch_id_count_post(id, count):
    """
    Specify the size of a batch
    Associate a service and ce with an item count
    :param id: Survey identifier
    :type id: str
    :param count: Number of items in batch
    :type count: int

    :rtype: None
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.define_batch(id, count)
    ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)


#
# /upload/{id}/{file}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def upload_id_file_post(id, file, files=None):
    """
    Upload collection instrument
    Upload a custom spreadsheet and insert into encrypted DB column
    :param id: Survey identifier
    :type id: str
    :param file: File name
    :type file: str
    :param files: The file to upload
    :type files: werkzeug.datastructures.FileStorage

    :rtype: None
    """
    bind_request_detail_to_log(request)
    uploaded_files = None
    for index in ['files', 'files[]', 'upfile']:
        if index in request.files:
            uploaded_files = request.files.getlist(index)

    if not uploaded_files:
        logger.error('No files supplied')
        return make_response('No files supplied', 500)

    count = 0
    for fileobject in uploaded_files:
        code, msg = collection_instrument.upload(id, fileobject, file)
        if code == 200:
            count += 1

    if count != len(uploaded_files):
        logger.warning('Uploaded {} of {}'.format(count, len(uploaded_files)))
        return make_response('Uploaded {} of {}'.format(count, len(uploaded_files)), 500)
    return make_response("OK", 200)


#
# /download_csv/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def download_csv_id_get(id):
    """
    Download CSV file
    Download a list of live spreadsheets
    :param id: Collection exercise identifier
    :type id: str

    :rtype: file
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.csv(id)
    ensure_log_on_error(code, msg)
    response = make_response(msg if type(msg) == str else msg['text'], code)
    response.headers["Content-Disposition"] = "attachment; filename=download.csv"
    response.headers["Content-type"] = "application/octet-stream"
    return response


#
# /activate/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def activate_id_put(id):
    """
    Activate batch
    Mark all items in the batch as available
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.activate(id)
    ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)


#
# /clear_batch/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def clear_batch_id_delete(id):
    """
    Clear a batch
    Clear down a batch definition, useful for testing
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.clear(id)
    ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)


#
# /download/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def download_id_get(id):
    """
    Download a file based on the id (RU_REF)
    Download a file (test routine)
    :param id: Respondent /Business identifier
    :type id: str

    :rtype: None
    """
    bind_request_detail_to_log(request)
    code, msg = collection_instrument.download(id)
    ensure_log_on_error(code, msg)
    response = make_response(msg if type(msg) == str else msg['text'], code)
    response.headers["Content-Disposition"] = "attachment; filename=download.png"
    response.headers["Content-type"] = "application/octet-stream"
    return response
