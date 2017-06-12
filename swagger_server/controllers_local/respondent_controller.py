##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from uuid import uuid4
from flask import jsonify, make_response, request
from structlog import get_logger
from .collectioninstrument import CollectionInstrument
from .ons_jwt import validate_jwt


collection_instrument = CollectionInstrument()
logger = get_logger()


def _ensure_log_on_error(code, msg):
    if code != 200:
        logger.info("Bad request", error_data=msg)


def _bind_request_detail_to_log():
    logger.bind(
        tx_id=str(uuid4()),
        method=request.method,
        path=request.full_path
    )
    logger.info("Start request")


# /collectioninstrument
#
@validate_jwt(['ci:read', 'ci:write'], request)
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
    _bind_request_detail_to_log()
    code, msg = collection_instrument.instruments(searchString)
    _ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)


#
# /collectioninstrument/id/{id}
#
@validate_jwt(['ci:read', 'ci:write'], request)
def get_collection_instrument_by_id(id):
    """
    Get a collection instrument by ID
    Returns a single collection instrument
    :param id: ID of collection instrument to return
    :type id: str

    :rtype: Collectioninstrument
    """
    _bind_request_detail_to_log()
    code, msg = collection_instrument.instrument(id)
    _ensure_log_on_error(code, msg)
    return make_response(jsonify(msg), code)
