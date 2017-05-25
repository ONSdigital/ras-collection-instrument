import connexion
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def static_typ_uri_get(typ, uri):
    """
    Style Sheets
    Serve Style sheets from this point
    :param typ: item type
    :type typ: str
    :param uri: path to serve
    :type uri: str

    :rtype: None
    """
    return 'do some magic!'
