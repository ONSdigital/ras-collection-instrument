from flask import *
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from flask import request, Response
import os
import sys
import hashlib
import ast
import psycopg2

from models import *

import uuid


# Enable cross-origin requests
app = Flask(__name__)
CORS(app)

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
u'classifiers': {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B'}},
{u'surveyId': u'urn:ons.gov.uk:id:survey:001.001.00002', u'urn': u'urn:ons.gov.uk:id:ci:001.001.00002',
u'reference': u'rsi-nonfuel', u'ciType': u'OFFLINE', u'classifiers': {u'RU_REF': u'01234567890'}}]
"""

if 'APP_SETTINGS' in os.environ:
    app.config.from_object(os.environ['APP_SETTINGS'])

# app.config.from_object("config.StagingConfig")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


def validate_uri(uri, id_type):
    """
    This function verifies if a resource uri string is in the correct
    format. it returns True or False. This function does not check
    if the uri is present in the database or not.

    :param uri: String
    :param id_type: String
    :return: Boolean
    """

    print "We are in validate_uri"

    print "Validating our URI: {}".format(uri)

    urn_prefix = 'urn'
    urn_ons_path = 'ons.gov.uk'
    urn_id_str = 'id'
    urn_overall_digit_len = 13
    urn_first_digit_len = 3
    urn_second_digit_len = 3
    urn_third_digit_len = 5

    try:

        arr = uri.split(':')
        sub_arr = arr[4].split('.')

        if arr[0] == urn_prefix \
                and arr[1] == urn_ons_path \
                and arr[2] == urn_id_str \
                and arr[3] == id_type \
                and len(arr[4]) == urn_overall_digit_len \
                and sub_arr[0].isdigit and len(sub_arr[0]) == urn_first_digit_len \
                and sub_arr[1].isdigit and len(sub_arr[1]) == urn_second_digit_len \
                and sub_arr[2].isdigit and len(sub_arr[2]) == urn_third_digit_len:
            print "URI is well formed': {}".format(uri[0:14])
            return True
        else:
            print "URI is malformed: {}. It should be: {}".format(uri[0:14], urn_ons_path)
            return False

    except:
        print "URI is malformed: {}. It should be: {}".format(uri[0:14], urn_ons_path)
        return False


@app.route('/collectioninstrument', methods=['GET'])
def collection():
    """
    This endpoint returns a filtered list of all the content fields for each collection
    instrument in the database.

    :return: Json Http Response
    """

    print "We are in collections"

    try:
        print "Making query to DB"
        a = CollectionInstrument.query.all()

    except exc.OperationalError:
        print "There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0])
        res = Response(response="""Error in the Collection Instrument DB, it looks like there
                       is no data presently or the DB is not available.
                       Please contact a member of ONS staff.""", status=500, mimetype="text/html")
        return res

    result = []
    for key in a:
        result.append(key.content)

    res_string = str(result)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp


@app.route('/collectioninstrument/file/<string:_id>', methods=['GET'])
def get_binary(_id):

    print "We are in get_binary"

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    try:
        # now filters on the unique indexed database column "urn"
        # should now only ever get 0 or 1 record here
        new_object = db.session.query(CollectionInstrument).filter(CollectionInstrument.urn == _id)[0]
    except:
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    if new_object.file_path is None:
        res = Response(response="No file present", status=404, mimetype="text/html")
        return res

    return send_from_directory('uploads', new_object.file_path)


# curl -X GET  http://localhost:5052/collectioninstrument/?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"}
@app.route('/collectioninstrument/', methods=['GET'])
def classifier():
    """
    This method performs a query on the content fields for each record,
    based on the value for the 'classifier' key in the json

    :return: Http Response
    """

    print "We are in classifier"

    query_classifier = request.args.get('classifier')       # get the query string from the URL.
    if query_classifier:
        try:
            query_dict = ast.literal_eval(query_classifier)  # convert our string into a dictionary
        except ValueError:
            # Something went wrong with our conversion, maybe they did not give us a valid dictionary?
            # Keep calm and carry on. Let the user know what they have to type to get this to work
            res = Response(response="""Bad input parameter.\n To search for a classifier your query string should
                                    look like: ?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"} """,
                                    status=400, mimetype="text/html")
            return res
    else:
        # We had no query string with 'classifier', let the user know what they should type.
        res = Response(response="""Bad input parameter.\n To search for a classifier your
                       query string should look like: ?classifier={"LEGAL_STATUS":"A","INDUSTRY":"B"}
                       """, status=400, mimetype="text/html")
        return res

    # Get a query set of all objects to search
    try:
        print "Making query to DB"
        collection_instruments = CollectionInstrument.query.all()

    except exc.OperationalError:
        print "There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0])
        res = Response(response="""Error in the Collection Instrument DB, it looks like
                       there is no data presently or the DB is not available.
                       Please contact a member of ONS staff.""", status=500, mimetype="text/html")
        return res

    # We are looking for matches for 'classifier' types which look like:
    # {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B', u'GEOGRAPHY': u'x'}
    # So we need to loop through our query string and our DB to do our matching
    # TODO Use sqlalchemy 'filter' to do all this. We should not be manually searching our DB
    matched_classifiers = []                                         # This will hold a list of our classifier objects

    # Loop through all objects and search for matches of classifiers
    for collection_instrument_object in collection_instruments:
        dict_classifier = collection_instrument_object.content['classifiers']
        match = False  # Make sure we set our match flag to false for each new object we check

        # Lets take a classifier dictionary e.g. {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B', u'GEOGRAPHY': u'x'}
        # And make sure all our query string classifiers are a match if we don't have them all then it's not a match.
        for queryVal in query_dict:
            try:
                if query_dict[queryVal] == dict_classifier[queryVal]:
                    match = True
                else:
                    # The dictionary item name does exist but it's value is different.
                    match = False
                    # print "*** NO MATCH FOR: ", queryDict[queryVal], " and ", dictClasifier[queryVal], "***"
                    break
            except KeyError:
                # The dictionary item does not exist in our dict so this is not a match either
                match = False
                # print "We don't have a key for: ", queryDict[queryVal]
                break

        if match:
            print " ***** Success We have a match for this object ****"
            matched_classifiers.append(collection_instrument_object.content)
    if matched_classifiers:
        print "We have some matches"
        for key in matched_classifiers:
            print key

    res_string = str(matched_classifiers)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp


@app.route('/collectioninstrument/id/<string:_id>', methods=['PUT'])
def add_binary(_id):

    """
    Get an existing collection instrument by Collection Instrument ID/URN.
    Modify the record, adding file path/UUID, then merge record back to the database.
    Plus, process the actual file to the file store.

    curl -X PUT --form "fileupload=@requirements.txt"  [URL]
    where [URL] == http://localhost:5000/collectioninstrument/id/a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11
    """

    print"We are in add_binary"

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    # now filters on the unique indexed database column "urn"
    # should now only ever get 0 or 1 record here
    existing_object = [[rec.id,
                        rec.urn,
                        rec.survey_urn,
                        rec.content,
                        rec.file_uuid,
                        rec.file_path]
                       for rec in CollectionInstrument.query.filter(CollectionInstrument.urn == _id)]

    uploaded_file = request.files['fileupload']

    if not os.path.isdir("uploads"):
        os.mkdir("uploads")

    new_uuid = str(uuid.uuid4())
    new_path = new_uuid + '_' + uploaded_file.filename
    uploaded_file.save('uploads/{}'.format(new_path))

    new_object = CollectionInstrument(id=existing_object[0][0],
                                      urn=existing_object[0][1],
                                      survey_urn=existing_object[0][2],
                                      content=existing_object[0][3],
                                      file_uuid=new_uuid,
                                      file_path=new_path)

    db.session.merge(new_object)
    db.session.commit()

    response = make_response("")
    etag = hashlib.sha1('/collectioninstrument/id/' + str(new_uuid)).hexdigest()
    response.set_etag(etag)

    return response, 201


@app.route('/collectioninstrument/', methods=['POST'])
def create():
    """
    This endpoint creates a collection instrument record, from the POST data

    :return: Http response
    """

    print "We are in create"

    collection_instruments = []

    json = request.json
    if json:
        response = make_response("")

        collection_instruments.append(request.json)
        response.headers["location"] = "/collectioninstrument/" + str(json["id"])

        try:
            json["id"]
            json["surveyId"]
            json["ciType"]
            print json["id"]
        except KeyError:
            res = Response(response="invalid input, object invalid", status=404, mimetype="text/html")
            return res

        if not validate_uri(json["id"], 'ci'):
            res = Response(response="invalid input, object invalid", status=404, mimetype="text/html")
            return res

        urn = json["id"]
        survey_urn = json["surveyId"]

        if not validate_uri(urn, 'ci'):
            res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
            return res

        if not validate_uri(survey_urn, 'survey'):
            res = Response(response="Invalid Survey ID supplied", status=400, mimetype="text/html")
            return res

        new_object = CollectionInstrument(urn=urn,
                                          survey_urn=survey_urn,
                                          content=json,
                                          file_uuid=None,
                                          file_path=None)

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
    """
    Locate a collection instrument by Collection Instrument ID/URN.
    This method is intended for locating collection instruments by a non-human-readable 'id'
    as opposed to by human-readable reference.

    :param _id: String
    :return: Http response
    """

    print "We are in get_id"

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    try:
        print "Querying DB"
        # now filters on the unique indexed database column "urn"
        object_list = [rec.content for rec in CollectionInstrument.query.filter(CollectionInstrument.urn == _id)]

    except exc.OperationalError:
        print "There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0])
        res = Response(response="""Error in the Collection Instrument DB, it looks like there is no data presently,
                                   or the DB is not available. Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
        return res

    if not object_list:
        print "object is empty"
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    for key in object_list:
        print "The id is: {}".format(key['id'])

        if not validate_uri(key['id'], 'ci'):
            res = Response(response="Invalid URI", status=400, mimetype="text/html")
            return res

    res = Response(response=str(object_list), status=200, mimetype="collection+json")
    return res


@app.route('/collectioninstrument/reference/<string:ci_ref>', methods=['GET'])
def get_ref(ci_ref):
    """
    Locate a collection instrument by reference.
    This method is intended for locating collection instruments by a human-readable 'reference'
    as opposed to by database Id.

    :param ci_ref: String
    :return: Http Response
    """

    print "We are in get_ref"

    try:
        print "Querying DB"
        object_list = [rec.content for rec in CollectionInstrument.query.all() if rec.content['reference'] == ci_ref]

    except exc.OperationalError:
        print "There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0])
        res = Response(response="""Error in the Collection Instrument DB, it looks like there is no data
                                presently or the DB is not available.
                                Please contact a member of ONS staff.""",
                                status=500, mimetype="text/html")
        return res

    if not object_list:
        print "object is empty"
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    res = Response(response=str(object_list), status=200, mimetype="collection+json")
    return res


@app.route('/collectioninstrument/surveyid/<string:survey_id>', methods=['GET'])
def get_survey_id(survey_id):
    """
    Locate a collection instrument by survey id/urn.
    :param survey_id: String
    :return: Http Response
    """

    print "We are in get_survey_id"

    if not validate_uri(survey_id, 'survey'):
        res = Response(response="Invalid URI", status=404, mimetype="text/html")
        return res

    try:
        print "Querying DB"
        # now filters on the indexed database column "survey_urn"
        object_list = [rec.content for rec in CollectionInstrument.query.filter(CollectionInstrument.survey_urn == survey_id)]

    except exc.OperationalError:
        print "There has been an error in the Collection Instrument DB. Exception is: {}".format(sys.exc_info()[0])
        res = Response(response="""Error in the Collection Instrument DB,
                                   it looks like there is no data presently or the DB is not available.
                                   Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
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
