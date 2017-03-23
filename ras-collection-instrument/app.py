"""
The main module which starts the server
"""

import ast
import hashlib
import os
import sys
import uuid
import logging
from logging import Formatter
from logging.handlers import RotatingFileHandler


from flask import request, Response, send_from_directory, make_response, jsonify, Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc
from jose import JWTError
from jwt import decode
from json import JSONEncoder

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

# NB this cirtular import needs resolving.
# There are ways of doing this, so we'll need to arrive at a decent solution.
from models import *


def validate_uri(uri, id_type):
    """
    This function verifies if a resource uri string is in the correct
    format. it returns True or False. This function does not check
    if the uri is present in the database or not.

    :param uri: String
    :param id_type: String
    :return: Boolean
    """

    app.logger.info("validate_uri uri: {}, id_type: {}".format(uri, id_type))
    app.logger.debug("Validating our URI: {}".format(uri))

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
            app.logger.debug("URI is well formed': {}".format(uri[0:14]))
            return True
        else:
            app.logger.warning("URI is malformed: {}. It should be: {}".format(uri[0:14], urn_ons_path))
            return False

    except:
        app.logger.warning("URI is malformed: {}. It should be: {}".format(uri[0:14], urn_ons_path))
        return False

def validate_scope(jwt_token, scope_type):
    """
    This function checks a jwt tokem for a required scope type.

    :param jwt_token: String
    :param scope_type: String
    :return: Boolean
    """

    app.logger.info("validate_scope jwt_token: {}, scope_type: {}".format(jwt_token, scope_type))

    # Make sure we can decrypt the token and it makes sense
    try:
        decrypted_jwt_token = decode(jwt_token)
        if decrypted_jwt_token['user_scopes']:
            for user_scope_list in decrypted_jwt_token['user_scopes']:
                if user_scope_list == scope_type:
                    app.logger.debug('Valid JWT scope.')
                    return True

        app.logger.warning('Invalid JWT scope.')
        return False

    except JWTError:
        app.logger.warning('JWT scope could not be validated.')
        return False

    except KeyError:
        app.logger.warning('JWT scope could not be validated.')
        return False


@app.route('/collectioninstrument', methods=['GET'])
def collection():
    """
    This endpoint returns a filtered list of all the content fields for each collection
    instrument in the database.

    :return: Json Http Response
    """

    app.logger.info("collectioninstrument hit")

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

    try:
        app.logger.debug("Making query to DB")
        object_list = [rec.content for rec in CollectionInstrument.query.all()]

    except exc.OperationalError:
        app.logger.error("There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB, it looks like there
                       is no data presently or the DB is not available.
                       Please contact a member of ONS staff.""", status=500, mimetype="text/html")
        return res

    if not object_list:
        app.logger.debug("object is empty")
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    jobject_list = JSONEncoder().encode(object_list)
    res = Response(response=jobject_list, status=200, mimetype="collection+json")
    return res


@app.route('/collectioninstrument/file/<string:_id>', methods=['GET'])
def get_binary(_id):

    app.logger.info("collectioninstrument/file file name is: {}".format(_id))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    try:
        # now filters on the unique indexed database column "urn"
        # should now only ever get 0 or 1 record here
        new_object = db.session.query(CollectionInstrument).filter(CollectionInstrument.urn == _id)[0]
    except:
        app.logger.error("There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0]))
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
    based on the value for the 'classifier' key in the json returned from the database.
    The method takes a query string in the GET HTTP request which it uses for it's query.

    :return: Http Response
    """

    app.logger.info("collectioninstrument/ endpoint")

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

    query_classifier = request.args.get('classifier')  # get the query string from the URL.
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
        app.logger.debug("Making query to DB")
        collection_instruments = CollectionInstrument.query.all()

    except:
        app.logger.error("There has been an error in our DB. Excption is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB, it looks like
                       there is no data presently or the DB is not available.
                       Please contact a member of ONS staff.""", status=500, mimetype="text/html")
        return res

    # We are looking for matches for 'classifier' types which look like:
    # {u'LEGAL_STATUS': u'A', u'INDUSTRY': u'B', u'GEOGRAPHY': u'x'}
    # So we need to loop through our query string and our DB to do our matching
    matched_classifiers = []  # This will hold a list of our classifier objects

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
            app.logger.debug(" ***** Success We have a match for this object ****")
            matched_classifiers.append(collection_instrument_object.content)
    if matched_classifiers:
        app.logger.debug("We have some matches")
        for key in matched_classifiers:
            print key

    res_string = str(matched_classifiers)
    resp = Response(response=res_string, status=200, mimetype="collection+json")
    return resp


@app.route('/collectioninstrument/id/<string:_id>', methods=['OPTIONS'])
def get_options(_id):
    """
    Locate a collection instrument by id/urn, returning the represenatation options available.
    :param _id: String
    :return: Http Response
    """
    app.logger.info("get_options with _id: {}".format(_id))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    # if request.headers.get('authorization'):
    #     jwt_token = request.headers.get('authorization')
    #     if not validate_scope(jwt_token, 'ci.read'):
    #         res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
    #         return res
    # else:
    #     res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
    #     return res

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid URI", status=404, mimetype="text/html")
        return res

    try:
        app.logger.debug("Querying DB in get_options")
        object_list = [[rec.content, rec.file_path] for rec in
                       CollectionInstrument.query.filter(CollectionInstrument.urn == _id)]

    except exc.OperationalError:
        app.logger.error("There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB,
                                   it looks like there is no data presently or the DB is not available.
                                   Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
        return res

    if not object_list:
        app.logger.info("Object list is empty for get_options")
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    app.logger.debug("Setting available representation options")
    if object_list[0][1] is None:
        representation_options = '{"representation options":["json"]}'
    else:
        representation_options = '{"representation options":["json","binary"]}'

    res = Response(response=str(representation_options), status=200, mimetype="collection+json")

    return res


@app.route('/collectioninstrument/id/<string:_id>', methods=['PUT'])
def add_binary(_id):
    """
    Get an existing collection instrument by Collection Instrument ID/URN.
    Modify the record, adding file path/UUID, then merge record back to the database.
    Plus, process the actual file to the file store.

    curl -X PUT --form "fileupload=@requirements.txt"  [URL]
    where [URL] == http://localhost:5000/collectioninstrument/id/urn:ons.gov.uk:id:ci:001.001.00002
    """

    app.logger.info("add_binary id value is: {}".format(_id))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.write'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

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

    app.logger.info("collectioninstrument/ create")

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.write'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

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
            app.logger.warning("""Collection Instrument POST did not contain correct mandatory
                               parameters in it's JSON payload: {}""".format(str(json)))
            res = Response(response="invalid input, object invalid", status=404, mimetype="text/html")
            return res

        if not validate_uri(json["id"], 'ci'):
            app.logger.warning("""Collection Instrument POST did not contain a valid URI
                               in the ID field. We receieved: {}""".format(json['id']))
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

    app.logger.info('get_id with value: {} '.format(_id))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

    if not validate_uri(_id, 'ci'):
        res = Response(response="Invalid ID supplied", status=400, mimetype="text/html")
        return res

    try:
        app.logger.debug('Querying DB')
        # now filters on the unique indexed database column "urn"
        object_list = [rec.content for rec in CollectionInstrument.query.filter(CollectionInstrument.urn == _id)]

    except exc.OperationalError:
        app.logger.error("There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB, it looks like there is no data presently,
                                   or the DB is not available. Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
        return res

    if not object_list:
        app.logger.debug("object is empty")
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    for key in object_list:
        app.logger.debug("The id is: {}".format(key['id']))

        if not validate_uri(key['id'], 'ci'):
            res = Response(response="Invalid URI", status=400, mimetype="text/html")
            return res

    jobject_list = JSONEncoder().encode(object_list[0])
    res = Response(response=jobject_list, status=200, mimetype="collection+json")
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

    app.logger.info("get_ref with ci_ref: {}".format(ci_ref))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res

    try:
        app.logger.debug("Querying DB")
        object_list = [rec.content for rec in CollectionInstrument.query.all() if rec.content['reference'] == ci_ref]

    except exc.OperationalError:
        app.logger.error("There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB, it looks like there is no data
                                presently or the DB is not available.
                                Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
        return res

    if not object_list:
        app.logger.debug("object is empty in function get_ref")
        res = Response(response="Collection instrument not found", status=404, mimetype="text/html")
        return res

    jobject_list = JSONEncoder().encode(object_list)
    res = Response(response=jobject_list, status=200, mimetype="collection+json")
    return res


# example command to search on just a survey urn:
# curl -X GET http://localhost:5052/collectioninstrument/surveyid/urn:ons.gov.uk:id:survey:001.001.00001

# command to search on a survey urn and a classifier:
# curl -X GET http://localhost:5052/collectioninstrument/surveyid/urn:ons.gov.uk:id:survey:001.001.00001?classifier={"classifiers": {"INDUSTRY": "R", "LEGAL_STATUS": "F", "GEOGRAPHY": "B"}}

@app.route('/collectioninstrument/surveyid/<string:survey_id>', methods=['GET'])
def get_survey_id(survey_id):
    """
    Locate a collection instrument by survey id/urn and optionally a classifier.
    :param survey_id: String, classifier: String
    :return: Http Response
    """

    app.logger.info("get_survey_id with survey_id: {}".format(survey_id))

    # First check that we have a valid JWT token if we don't send a 400 error with authorisation failure
    if request.headers.get('authorization'):
        jwt_token = request.headers.get('authorization')
        if not validate_scope(jwt_token, 'ci.read'):
            res = Response(response="Invalid token/scope to access this Microservice Resource", status=400, mimetype="text/html")
            return res
    else:
        res = Response(response="Valid token/scope is required to access this Microservice Resource", status=400, mimetype="text/html")
        return res
    if not validate_uri(survey_id, 'survey'):
        res = Response(response="Invalid URI", status=404, mimetype="text/html")
        return res

    try:
        app.logger.debug("Querying DB in get_survey_id")

        search_string = request.args.get('classifier')

        if search_string is not None:
            # search with the survey urn and the search string
            app.logger.debug("Querying DB with survey urn and search string: {} {}".format(survey_id, search_string))
            object_list = [rec.content for rec in
                           CollectionInstrument.query
                           .filter(CollectionInstrument.survey_urn == survey_id)
                           .filter(CollectionInstrument.content.op('@>')(search_string)).all()]
        else:
            # search with just the survey urn
            app.logger.debug("Querying DB with survey urn:{}".format(survey_id))
            object_list = [rec.content for rec in
                           CollectionInstrument.query
                           .filter(CollectionInstrument.survey_urn == survey_id)]

    except exc.OperationalError:
        app.logger.error("There has been an error in our DB. Exception is: {}".format(sys.exc_info()[0]))
        res = Response(response="""Error in the Collection Instrument DB,
                                   it looks like there is no data presently or the DB is not available.
                                   Please contact a member of ONS staff.""",
                       status=500, mimetype="text/html")
        return res

    if not object_list:
        app.logger.info("Object list is empty for get_survey_id")
        res = Response(response="Collection instrument(s) not found", status=404, mimetype="text/html")
        return res

    jobject_list = JSONEncoder().encode(object_list)
    res = Response(response=jobject_list, status=200, mimetype="collection+json")
    return res


if __name__ == '__main__':
    # Create a file handler to handle our logging
    handler = RotatingFileHandler('application.log', maxBytes=10000, backupCount=1)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    handler.setFormatter(Formatter('%(asctime)s %(levelname)s: %(message)s ' '[in %(pathname)s:%(lineno)d]'))
    # Initialise SqlAlchemy configuration here to avoid circular dependency
    db.init_app(app)

    # Run
    app.run(port=5052, debug=False)
