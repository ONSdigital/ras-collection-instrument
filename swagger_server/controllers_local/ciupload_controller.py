##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   Date:    11 May 2017                                                     #
#   Author:  Gareth Bult                                                     #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################

import os
from flask import request, jsonify, make_response
from .collectioninstrument import CollectionInstrument

root_folder = os.getcwd()
collection_instrument = CollectionInstrument()


#
# /status/{id}
#
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


# /upload/{id}/{file}
#
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
    return jsonify({'count': count})


#
# /download_csv/{id}
#
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
# /download/{ru_ref}
#
def download_ru_ref_get(ru_ref):
    """
    Download a file based on the RU_REF
    Download a file (test routine)
    :param ru_ref: Respondent /Business identifier
    :type ru_ref: str

    :rtype: None
    """

#
# /download/{id}
#
def download_id_get(id):
    """
    Download a file based on the id (RU_REF)
    Download a file (test routine)
    :param id: Respondent /Business identifier
    :type id: str

    :rtype: None
    """
    code, msg = collection_instrument.download(id)
    response = make_response(msg if type(msg) == str else msg['text'], code)
    response.headers["Content-Disposition"] = "attachment; filename=download.png"
    response.headers["Content-type"] = "application/octet-stream"
    return response
