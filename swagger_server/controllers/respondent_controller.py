import connexion
from swagger_server.models.collectioninstrument import Collectioninstrument
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


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
    return 'do some magic!'


def get_collection_instrument_by_id(id):
    """
    Get a collection instrument by ID
    Returns a single collection instrument
    :param id: ID of collection instrument to return
    :type id: str

    :rtype: Collectioninstrument
    """
    return 'do some magic!'


def survey_responses_case_id_get(case_id):
    """
    Get a survey response by case ID
    Returns a survey response
    :param case_id: ID of case
    :type case_id: str

    :rtype: None
    """
    return 'do some magic!'


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
    return 'do some magic!'
