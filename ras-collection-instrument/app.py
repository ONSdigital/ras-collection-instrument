from flask import *
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from flask import request
import os
import sys
import hashlib
import ast
import psycopg2
from uuid import UUID

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

from models import *

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
    print "We are in collections"
    try:
        print "Making query to DB"
        a = Result.query.all()

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB, it looks like there is no data presently or the DB is not available. Please contact a member of ONS staff.", status=500, mimetype="text/html")
        return res

    result = []
    for key in a:
        result.append(key.content)

    res_string = str(result)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp

#curl -X GET  http://localhost:5052/collectioninstrument/?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"}
@app.route('/collectioninstrument/', methods=['GET'])
def classifier():
    print "We are in classifier"
    queryClassifer = request.args.get('classifier')                                 # get the query string from the URL.
    if queryClassifer:
        try:
            queryDict = ast.literal_eval(queryClassifer)                            # convert our string into a dictionary
        except ValueError:
            # Something went wrong with our conversion, maybe they did not give us a valid dictionary? Keep calm and carry on. Let the user know what they have to type to get this to work
            res = Response(response='Bad input parameter.\n To search for a classifier your querry string should look like: ?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"} ', status=400, mimetype="text/html")
            return res
    else:
        # We had no query string with 'classifier', let the user know what they should type.
        res = Response(response='Bad input parameter.\n To search for a classifier your querry string should look like: ?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"} ', status=400, mimetype="text/html")
        return res

    # Get a query set of all objects to search
    try:
        print "Making query to DB"
        collection_instruments = Result.query.all()
        #collection_instruments = [x.content for x in Result.query.all() if x.content['classifier']]

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB, it looks like there is no data presently or the DB is not available. Please contact a member of ONS staff.", status=500, mimetype="text/html")
        return res

    # We are looking for matches for 'classifier' types which look like: {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B', u'GEOGRAPHY': u'x'}
    # So we need to loop through our query string and our DB to do our matching
    # TODO Use sqlalcemy 'filter' to do all this. We should not be manually searching our DB
    matchedclasifiers =[]                                                       # This will hold a list of our classifier objects
    for collection_instrument_object in collection_instruments:                 # Loop through all objects and search for matches of classifiers
        dictClasifier = collection_instrument_object.content['classifiers']
        match = False # Make sure we set our match flag to false for each new object we check

        # Lets take a classifier dictionary e.g. {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B', u'GEOGRAPHY': u'x'}
        # And make sure all our query string classifiers are a match if we don't have them all then it's not a match.
        for queryVal in queryDict:
            try:
                if queryDict[queryVal] == dictClasifier[queryVal]:
                    match = True
                else:
                    # The dictionary item name does exist but it's value is different.
                    match = False
                    #print "*** NO MATCH FOR: ", queryDict[queryVal], " and ", dictClasifier[queryVal], "***"
                    break
            except KeyError:
                # The dictionary item does not exist in our dict so this is not a match either
                match = False
                #print "We don't have a key for: ", queryDict[queryVal]
                break

        if match:
            print " ***** Success We have a match for this object ****"
            matchedclasifiers.append(collection_instrument_object.content)
    if matchedclasifiers:
        print "We have some matches"
        for key in matchedclasifiers:
            print key

    res_string = str(matchedclasifiers)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp


#curl -X PUT --form "fileupload=@requirements.txt"  http://localhost:5000/collectioninstrument/id/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
@app.route('/collectioninstrument/id/<string:file_uuid>', methods=['PUT'])
def add_binary(file_uuid):

    try:
        new_object = db.session.query(Result).filter(Result.file_uuid==file_uuid)[0]#.first()
    except:
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    uploaded_file = request.files['fileupload']

    if not os.path.isdir("uploads"):
        os.mkdir("uploads")

    newpath = str(uuid.uuid4()) +uploaded_file.filename
    uploaded_file.save('uploads/{}'.format(newpath ))

    new_object.file_path = newpath

    db.session.add(new_object)
    db.session.commit()

    response = make_response("")
    etag = hashlib.sha1('/collectioninstrument/id/'+ str(file_uuid)).hexdigest()
    response.set_etag(etag)

    return response, 201


@app.route('/collectioninstrument', methods=['POST'])
def create():
    print "We are in create"
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
        res = Response(response="Invalide ID supplied", status=400, mimetype="text/html")
        return res

    try:
        print "Making query to DB"
        object_list = [x.content for x in Result.query.all() if x.content['id'] == _id]

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB, it looks like there is no data presently, or the DB is not available. "
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
            res = Response(response="Invalide URI", status=400, mimetype="text/html")
            return res

    res = Response(response=str(object_list), status=200, mimetype="collection+json")
    return res


@app.route('/collectioninstrument/<string:file_uuid>', methods=['GET'])
def get_ref(file_uuid):
    print "we are in get_ref"
    """ Locate a collection instrument by reference.

    This method is intended for locating collection instruments by a human-readable 'reference'
    as opposed to by database Id.
    """
    # We need to determine the application type from the header. Business logic dictates that we provide the correct
    # response by what type is set (i.e if the application type is a spread sheet we should only provide OFF LINE,
    # if it's JSON we should provide ON-LINE collection instrument

    #content-type-requested = request.headers['content-type']
    #print "This request is asking for content type of: {}".format(content-type-requested)
    #TODO Use this variable 'content-type-requested' to ensure we use the correct collection instrument

    try:
        print "Making query to DB"
        object_list = [x.content for x in Result.query.all() if x.content['reference'] == file_uuid]

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="Error in the Collection Instrument DB, it looks like there is no data presently or the DB is not available. Please contact a member of ONS staff.", status=500, mimetype="text/html")
        return res

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
        res = Response(response="Error in the Collection Instrument DB, it looks like there is no data presently or the DB is not available. Please contact a member of ONS staff.", status=500, mimetype="text/html")
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
