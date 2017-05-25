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
# /collectioninstrument
#
def collectioninstrument_get(searchString=None, skip=None, limit=None):
    """
    searches collection instruments
    By passing in the appropriate options, you can search for available collection instruments 
    :param searchString: pass an optional search string for looking up collection instruments based on classifier
    :type searchString: str
    :param skip: number of records to skip for pagination
    :type skip: int
    :param limit: maximum number of records to return
    :type limit: int

    :rtype: None
    """
    code, msg = collection_instrument.instruments(searchString)
    return make_response(jsonify(msg), code)

#
# /collectioninstrument/id/{id}
#
def get_collection_instrument_by_id(id):
    """
    Get a collection instrument by ID
    Returns a single collection instrument
    :param id: ID of collection instrument to return
    :type id: str

    :rtype: Collectioninstrument
    """
    code, msg = collection_instrument.instrument(id)
    return make_response(jsonify(msg), code)
