##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from flask import jsonify, make_response, request
from .collectioninstrument import CollectionInstrument
from ons_ras_common.ons_decorators import validate_jwt, before_request
from .survey_response import SurveyResponse

collection_instrument = CollectionInstrument()

#
# /collectioninstrument
#


@before_request(request)
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
    code, msg = collection_instrument.instruments(searchString)
    return make_response(jsonify(msg), code)


#
# /collectioninstrument/id/{id}
#
@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
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

#
# /survey_responses/{case_id}
#


@before_request(request)
@validate_jwt(['ci:read', 'ci:write'], request)
def survey_responses_case_id_post(case_id, file=None):
    """
    Upload from the respondent
    The survey response file with the case id as identifier
    :param case_id: Case id identifier
    :type case_id: str
    :param file: The file to upload
    :type file: werkzeug.datastructures.FileStorage

    :rtype: None
    """
    code, msg = SurveyResponse().add_survey_response(case_id, file)
    return make_response(msg, code)
