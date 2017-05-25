import os
from flask import send_from_directory

root_folder = os.getcwd()
#
# /static/{typ}/{uri}
#
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
    directory = '{}/static/{}'.format(root_folder, typ)
    return send_from_directory(directory, uri)

#
# /upload
#
#def upload_get():
#    """
#    Get test page
#    Get the test upload page
#
#    :rtype: None
#    """
#    return send_from_directory('{}/static/html'.format(root_folder), 'index.html')
