from flask import *
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from flask import request
from models import *
import os
import sys
import hashlib

# Enable cross-origin requests
app = Flask(__name__)
CORS(app)

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

if 'APP_SETTINGS' in os.environ:
    app.config.from_object(os.environ['APP_SETTINGS'])

# app.config.from_object("config.StagingConfig")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Utility class for parsing URL/URI this checks we conform to ONS URI
def validateURI(uri, idType):
    print "Validating our URI: {}".format(uri)

    urnPrefix = 'urn'
    urnONSpath = 'ons.gov.uk'
    urnIdStr = 'id'
    urnOverallDigitLen = 13
    urnFirstDigitLen = 3
    urnSecondDigitLen = 3
    urnThirdDigitLen = 5

    try:

        arr = uri.split(':')
        sub_arr = arr[4].split('.')

        if arr[0] == urnPrefix \
                and arr[1] == urnONSpath \
                and arr[2] == urnIdStr \
                and arr[3] == idType \
                and len(arr[4]) == urnOverallDigitLen \
                and sub_arr[0].isdigit and len(sub_arr[0]) == urnFirstDigitLen \
                and sub_arr[1].isdigit and len(sub_arr[1]) == urnSecondDigitLen \
                and sub_arr[2].isdigit and len(sub_arr[2]) == urnThirdDigitLen:
            print "URI is well formed': {}".format(uri[0:14])
            return True
        else:
            print "URI is malformed: {}. It should be: {}".format(uri[0:14], urnONSpath)
            return False

    except:
        print "URI is malformed: {}. It should be: {}".format(uri[0:14], urnONSpath)
        return False


@app.route('/collectioninstrument', methods=['GET'])
def collection():
    print "help"
    a = Result.query.all()
    result = []
    for key in a:
        result.append(key.content)

    res_string = str(result)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp


@app.route('/collectioninstrument', methods=['POST'])
def create():
    json = request.json
    if json:
        response = make_response("")

        collection_instruments.append(request.json)
        #json["id"] = len(collection_instruments)
        response.headers["location"] = "/collectioninstrument/" + str(json["id"])

        try:
            json["id"]
            json["surveyId"]
            json["ciType"]
            print json["id"]
        except KeyError:
            res = Response(response="invalid input, object invalid", status=404, mimetype="text/html")
            return res

        if not validateURI(json["id"],'ci'):
            res = Response(response="invalid input, object invalid", status=404, mimetype="text/html")
            return res

        new_object = Result(content=json, file_uuid=None)
        db.session.add(new_object)
        db.session.commit()

        collection_path = response.headers["location"] = "/collectioninstrument/" + str(new_object.id)

        etag = hashlib.sha1(collection_path).hexdigest()

        response.set_etag(etag)

        response.headers["location"] = "/collectioninstrument/" + str(new_object.id)
        return response, 201
    return jsonify({"message": "Please provide a valid Json object.",
                    "hint": "you may need to pass a content-type: application/json header"}), 400


@app.route('/collectioninstrument/id/<string:_id>', methods=['GET'])
def get_id(_id):
    """ Locate a collection instrument by row ID.

    This method is intended for locating collection instruments by a non-human-readable 'id'
    as opposed to by human-readable reference.
    """
    # We need to determine the application type from the header. Business logic dictates that we provide the correct
    # response by what type is set (i.e if the application type is a spread sheet we should only provide OFF LINE,
    # if it's JSON we should provide ON-LINE collection instrument
    # content-type-requested = request.headers['content-type']
    # print "This request is asking for content type of: {}".format(content-type-requested)
    # TODO Use this variable 'content-type-requested' to ensure we use the correct collection instrument

    # object = Result.query.get_or_404(_id)

    if not validateURI(_id, 'ci'):
        res = Response(response="Invalide URI", status=404, mimetype="text/html")
        return res

    try:
        print "Making query to DB"
        object_list = [x.content for x in Result.query.all() if x.content['id'] == _id]

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB, it looks there is no data presently. "
                                "Please contact a member of ONS staff.", status=500, mimetype="text/html")
        return res

    # print "The URI is: {}".format(object_list)

    if not object_list:
        print "object is empty"
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    for key in object_list:
        print "The id is: {}".format(key['id'])
        if not validateURI(key['id'], 'ci'):
            res = Response(response="Invalide URI", status=404, mimetype="text/html")
            return res

    # print object_list

    res = Response(response=str(object_list), status=200, mimetype="collection+json")

    # res = Response(response=str(object_string),status=200, mimetype="collection+json")

    return res


@app.route('/collectioninstrument/<string:file_uuid>', methods=['GET'])
def get_ref(file_uuid):
    """ Locate a collection instrument by reference.

    This method is intended for locating collection instruments by a human-readable 'reference'
    as opposed to by database Id.
    """
    # We need to determine the application type from the header. Business logic dictates that we provide the correct
    # response by what type is set (i.e if the application type is a spread sheet we should only provide OFF LINE,
    # if it's JSON we should provide ON-LINE collection instrument
    # content-type-requested = request.headers['content-type']
    print "This request is asking for content type of: {}".format(content - type - requested)
    # TODO Use this variable 'content-type-requested' to ensure we use the correct collection instrument

    object_list = [x.content for x in Result.query.all() if x.content['reference'] == file_uuid]

    if not object_list:
        print "object is empty"
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    res = Response(response=str(object_list), status=200, mimetype="collection+json")
    return res


@app.route('/collectioninstrument/surveyid/<string:surveyId>', methods=['GET'])
def get_surveyId(surveyId):
    """
    Locate a collection instrument by survey urn.
    """

    if not validateURI(surveyId, 'survey'):
        res = Response(response="Invalide URI", status=404, mimetype="text/html")
        return res

    try:
        print "Querying DB..."
        object_list = [x.content for x in Result.query.all() if x.content['surveyId'] == surveyId]

    except exc.OperationalError:
        print "There has been an error in the Collection Instrument DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB", status=500, mimetype="text/html")
        return res

    if not object_list:
        print "Object is empty"
        res = Response(response="Collection instrument(s) not found", status=404, mimetype="text/html")
        return res

    res = Response(response=str(object_list), status=200, mimetype="collection+json")

    return res


if __name__ == '__main__':
    # Initialise SqlAlchemy configuration here to avoid circular dependency
    db.init_app(app)

    # Run
    app.run(port=5052)
