##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from flask import request, jsonify, make_response
from .collectioninstrument import CollectionInstrument
from ons_ras_common.ons_decorators import validate_jwt, before_request

collection_instrument = CollectionInstrument()


@validate_jwt(['ci:read', 'ci:write'], request)
def instrument_size_get(id):
    """
    Recover the size of a collection instrument
    :param id:
    :return: size
    """
    code, msg = collection_instrument.instrument_size(id)
    return make_response(jsonify(msg), code)


#
# /status/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def status_id_get(id):
    """
    Get upload status
    Return a count of items thus far and total in batch
    :param id: Survey identifier
    :type id: str

    :rtype: None
    """
    code, msg = collection_instrument.status(id)
    return make_response(jsonify(msg), code)


#
# /define_batch/{id}/{count}
#
@before_request(request)
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
    code, msg = collection_instrument.define_batch(id, count)
    return make_response(jsonify(msg), code)


#
# /upload/{id}/{file}
#
@before_request(request)
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
    uploaded_files = None
    for index in ['files', 'files[]', 'upfile']:
        if index in request.files:
            uploaded_files = request.files.getlist(index)

    if not uploaded_files:
        return make_response('No files supplied', 500)

    count = 0
    for fileobject in uploaded_files:
        code, msg = collection_instrument.upload(id, fileobject, file)
        if code == 200:
            count += 1

    if count != len(uploaded_files):
        return make_response('Uploaded {} of {}'.format(count, len(uploaded_files)), 500)
    return make_response("OK", 200)


#
# /download_csv/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def download_csv_id_get(id):
    """
    Download CSV file
    Download a list of live spreadsheets
    :param id: Collection exercise identifier
    :type id: str

    :rtype: file
    """
    code, msg = collection_instrument.csv(id)
    response = make_response(msg if type(msg) == str else msg['text'], code)
    response.headers["Content-Disposition"] = "attachment; filename=download.csv"
    response.headers["Content-type"] = "application/octet-stream"
    return response


#
# /activate/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def activate_id_put(id):
    """
    Activate batch
    Mark all items in the batch as available
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    code, msg = collection_instrument.activate(id)
    return make_response(jsonify(msg), code)


#
# /clear_batch/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def clear_batch_id_delete(id):
    """
    Clear a batch
    Clear down a batch definition, useful for testing
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    code, msg = collection_instrument.clear(id)
    return make_response(jsonify(msg), code)


#
# /clear_ruref/{re_ref}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def clear_ruref(ru_ref):
    """
    Clear an instrument by ru_ref, useful for testing
    :param ru_ref: Collection exercise identifier
    :type ru_ref: str

    :rtype: None
    """
    code, msg = collection_instrument.clear_by_ref(ru_ref)
    return make_response(jsonify(msg), code)

#
# /download/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def download_id_get(id):
    """
    Download a file based on the id (Instrument ID)
    Download a file (test routine)
    :param id: Collection instrument ID
    :type id: str

    :rtype: None
    """
    args = collection_instrument.download(id)
    code = args[0]
    msg = args[1]
    response = make_response(msg, code)
    if code == 200:
        response.headers["Content-Disposition"] = "attachment; filename={}.xlsx".format(args[2])
        response.headers["Content-type"] = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return response
