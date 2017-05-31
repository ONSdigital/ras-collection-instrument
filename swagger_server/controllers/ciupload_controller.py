import connexion
from datetime import date, datetime
from typing import List, Dict
from six import iteritems
from ..util import deserialize_date, deserialize_datetime


def activate_id_put(id):
    """
    Activate batch
    Mark all items in the batch as available
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def clear_batch_id_delete(id):
    """
    Clear a batch
    Clear down a batch definition, useful for testing
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def define_batch_id_count_post(id, count):
    """
    Specify the size of a batch
    Associate a service and ce with an item count
    :param id: Collection exercise identifier
    :type id: str
    :param count: Number of items in batch
    :type count: int

    :rtype: None
    """
    return 'do some magic!'


def download_csv_id_get(id):
    """
    Download CSV file
    Download a list of live spreadsheets
    :param id: Collection exercise identifier
    :type id: str

    :rtype: file
    """
    return 'do some magic!'


def download_id_get(id):
    """
    Download a file based on the id (RU_REF)
    Download a file (test routine)
    :param id: Respondent /Business identifier
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def status_id_get(id):
    """
    Get upload status
    Return a count of items thus far and total in batch
    :param id: Collection exercise identifier
    :type id: str

    :rtype: None
    """
    return 'do some magic!'


def upload_id_file_post(id, file, files=None):
    """
    Upload collection instrument
    Upload a custom spreadsheet and insert into encrypted DB column
    :param id: Collection exercise identifier
    :type id: str
    :param file: File name
    :type file: str
    :param files: The file to upload
    :type files: werkzeug.datastructures.FileStorage

    :rtype: None
    """
    return 'do some magic!'
