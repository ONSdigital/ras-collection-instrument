from flask import *
#from flask_cors import CORS
from flask.ext.sqlalchemy import SQLAlchemy
#from models import Result
import os

# Enable cross-origin requests
app = Flask(__name__)
#CORS(app)

collection_instruments = []

#
# http://docs.sqlalchemy.org/en/latest/core/type_basics.html
#
# data_table = Table('data_table', metadata,
#    Column('id', Integer, primary_key=True),
#    Column('data', JSON)
# )
#
"""
[{u'surveyId': u'urn:ons.gov.uk:id:survey:001.001.00001',
u'urn': u'urn:ons.gov.uk:id:ci:001.001.00001', u'reference': u'rsi-nonfuel', u'ciType': u'ONLINE',
u'classifiers': {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B'}},{u'surveyId': u'urn:ons.gov.uk:id:survey:001.001.00002', u'urn': u'urn:ons.gov.uk:id:ci:001.001.00002',
u'reference': u'rsi-nonfuel', u'ciType': u'OFFLINE', u'classifiers': {u'RU_REF': u'01234567890'}}]
"""

app.config.from_object(os.environ['APP_SETTINGS'])

#app.config.from_object("config.StagingConfig")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

import uuid
from models import *

print "before"
#i#mport json
#a = Result.query.all()
#print a

print "after"

@app.route('/collectioninstrument', methods=['GET'])
def collection():

    print "help"
    a = Result.query.all()
    result = []
    for key in a:
        result.append(key.content)

    res_string = str(result)
    resp = Response(response=res_string,status=200, mimetype="collection+json")
    return resp



@app.route('/collectioninstrument', methods=['POST'])
def create():
    json = request.json
    if json:
        response = make_response("")
        collection_instruments.append(request.json)
        json["id"] = len(collection_instruments)
        response.headers["location"] = "/collectioninstrument/" + str(json["id"])
        return response, 201
    return jsonify({"message": "Please provide a valid Json object.",
                    "hint": "you may need to pass a content-type: application/json header"}), 400


@app.route('/collectioninstrument/id/<int:_id>', methods=['GET'])
def get_id(_id):
    """ Locate a collection instrument by row ID.

    This method is intended for locating collection instruments by a non-human-readable 'id'
    as opposed to by human-readable reference.
    """
    object = Result.query.get_or_404(_id)

    object_string = object.content


    print object_string
    res = Response(response=str(object_string),status=200, mimetype="collection+json")
    return res



@app.route('/collectioninstrument/<string:file_uuid>', methods=['GET'])
def get_ref(file_uuid):
    """ Locate a collection instrument by reference.

    This method is intended for locating collection instruments by a human-readable 'reference'
    as opposed to by database Id.
    """


    object_list = [x.content for x in Result.query.all() if x.content['reference'] == file_uuid]

    res = Response(response=str(object_list),status=200, mimetype="collection+json")

    return res



app.run(port=5051)

