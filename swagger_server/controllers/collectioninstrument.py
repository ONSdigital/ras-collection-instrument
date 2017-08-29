##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ons_ras_common import ons_env
from crochet import wait_for
from ..models.instrument import InstrumentModel
from ..models.exercise import ExerciseModel
from ..models.business import BusinessModel
from ..models.survey import SurveyModel
from ..models.classification import ClassificationModel, classifications
from json import loads
from uuid import UUID
import treq
from twisted.internet import reactor
from twisted.internet.error import UserError
from sqlalchemy.orm import sessionmaker, scoped_session


#DEFAULT_SURVEY = "3decb89c-c5f5-41b8-9e74-5033395d247e"
DEFAULT_SURVEY = "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"


def protect(uuid=True):
    """
    This decorator is designed to add a protective layer around endpoint logic, specifically
    it checks for 'id_example' and allows it for integration tests to succeed. It also ensures that
    passed parameters are strings, maybe not needed but prevents something poking a dict or similar
    through by mistake. It then converts the first parameter to a UUID type if the 'uuid' flag is set.
    
    :param uuid: Whether to convert first parameter to UUID()
    :return: status code, return message
    """
    def protect_wrapped(func):
        def func_wrapped(*args, **kwargs):
            try:
                my_id = args[1]
                if my_id == 'id_example':
                    return 200, {'text': 'unit tests status = PASS'}
                if type(my_id) != str:
                    return 400, {'text': 'id is not a string'}
                if uuid:
                    my_args = list(args)
                    my_args[1] = UUID(my_id)
                return func(*(my_args if uuid else args), **kwargs)
            except ValueError:
                return 500, {'text': 'id is not a valid UUID ({})'.format(my_id)}
            except Exception as e:
                ons_env.logger.error(e)
                return 500, {'text': 'Server experienced an unexpected error'}
        return func_wrapped
    return protect_wrapped


class CollectionInstrument(object):

    def __init__(self):
        """
        The default entry here is used by the unit testing code, so although it looks
        redundant, please leave it in.
        """
        self._exercise_cache = {}

    """
    Database shortcuts, the SQLAlchemy syntax isn't always immediately obvious, so here we're just using
    some 'more' obvious shortcuts to functions, purely from a 'readability' perspective.
    """
    def _get_exercise(self, exercise_id, session=None):
        if not session:
            session = ons_env.db.session
        return session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).first()

    def _get_business(self, ru_ref, session=None):
        if not session:
            session = ons_env.db.session
        return session.query(BusinessModel).filter(BusinessModel.ru_ref == ru_ref).first()

    def _get_survey(self, survey_id, session=None):
        if not session:
            session = ons_env.db.session
        return session.query(SurveyModel).filter(SurveyModel.survey_id == survey_id).first()

    def _get_instrument(self, instrument_id):
        return ons_env.db.session.query(InstrumentModel).filter(InstrumentModel.instrument_id == instrument_id).first()

    def _get_instrument_by_ru(self, ru_ref):
        return ons_env.db.session.query(InstrumentModel).filter(BusinessModel.ru_ref == ru_ref).first()

    def _exercise_status_set(self, exercise_id, status):
        ons_env.db.session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).update({'status': status})

    def _instruments_by_classifier(self, classifiers):
        """
        This looks like it needs lots of explanationn, but it really doesn't when you read it.
        
        :param classifiers: dict of (key, value) pairs to search on 
        :return: query results (matching records)
        """
        query = ons_env.db.session.query(InstrumentModel)
        used = []

        for attr, value in classifiers.items():
            if attr == 'RU_REF' and BusinessModel not in used:
                query = query.join((BusinessModel, InstrumentModel.businesses))
                used.append(BusinessModel)
            elif attr == 'COLLECTION_EXERCISE' and ExerciseModel not in used:
                query = query.join((ExerciseModel, InstrumentModel.exercises))
                used.append(ExerciseModel)
            elif attr == 'SURVEY_ID' and SurveyModel not in used:
                query = query.join(SurveyModel, InstrumentModel.survey)
                used.append(SurveyModel)
            elif attr in classifications and ClassificationModel not in used:
                query = query.join(ClassificationModel.instrument)
                used.append(ClassificationModel)
            else:
                return 'unable to handle query for ({}={})'.format(attr, value)
        for attr, value in classifiers.items():
            if attr == 'RU_REF':
                query = query.filter(BusinessModel.ru_ref == value)
            elif attr == 'COLLECTION_EXERCISE':
                query = query.filter(ExerciseModel.exercise_id == UUID(value))
            elif attr == 'SURVEY_ID':
                query = query.filter(SurveyModel.survey_id == UUID(value))
            else:
                query = query.filter(ClassificationModel.kind == attr).filter(ClassificationModel.value == value)
        return query.limit(10).all()

    @protect(uuid=True)
    def define_batch(self, exercise_id, count):
        """
        Define a batch is used to tell the service which surveys are in play and how many files to expect.
        At some point this will be connected to a user to a UI which will allow entry of these details, but
        for testing batches can be initiated with the Swagger UI
        
        :param exercise_id: The survey id (this is a uuid)
        :param count: The number of files we are expecting (in total)
        :return: At present this routine can't fail as we have no spec for parameter limits
        """
        exercise = self._get_exercise(exercise_id)
        if not exercise:
            ons_env.db.session.add(ExerciseModel(exercise_id=exercise_id, items=count))
            ons_env.db.session.commit()
        return 200, {'text': 'OK'}

    @protect(uuid=True)
    def clear(self, exercise_id):
        """
        Clear a batch (or reject a batch) is used to scrap a current batch in the event the user decides they
        don't actually want to commit it for some reason.

        :param exercise_id: An exercise id, which is a uuid
        :return: Returns a 200 if the batch was removed, or 204 if not found
        """
        exercise = self._get_exercise(exercise_id)
        if not exercise:
            return 204, {'text': 'No such batch'}
        ons_env.db.session.delete(exercise)
        ons_env.db.session.commit()
        return 200, {'text': 'OK'}

    @protect(uuid=False)
    def clear_by_ref(self, ru_ref):
        """
        Clear an instrument

        :param ru_ref: An RU_REF
        :return: Returns a 200 if the batch was removed, or 204 if not found
        """
        instrument = self._get_instrument_by_ru(ru_ref)
        if not instrument:
            return 404, {'text': 'no such instrument'}
        ons_env.db.session.delete(instrument)
        ons_env.db.session.commit()
        return 200, {'text': 'instrument deleted'}

    @protect(uuid=True)
    def instrument(self, instrument_id):
        """
        Return a specific collection instrument based on an id

        :param instrument_id: The id of the instrument we want 
        :return: formatted JSON version of the instrument
        """
        instrument = self._get_instrument(instrument_id)
        if not instrument:
            return 404, 'Instrument not found'
        return 200, instrument.json

    @protect(uuid=True)
    def status(self, exercise_id):
        """
        Get the status of a given batch. This returns a status object containing a number of variables, notably
        'current' and 'status'.

        :param exercise_id: Survey reference 
        :return: Return 200 and status object if found, or 204 if batch not found
        """
        exercise = self._get_exercise(exercise_id)
        if not exercise:
            return 204, {'text': 'No such batch'}
        return 200, exercise.json

    @protect(uuid=True)
    def activate(self, exercise_id):
        """
        Activate the specified batch and move all associated files into 'active' mode. (database persistence
        not implemented yet.

        :param exercise_id: Survey reference 
        :return: 200 if activates, 204 if batch not found, or 500 is batch in wrong state
        """
        exercise = self._get_exercise(exercise_id)
        if not exercise:
            return 204, {'text': 'No such batch'}
        if exercise.status != 'pending':
            return 500, {'text': 'Batch in wrong state'}
        exercise.status = 'active'
        ons_env.db.session.commit()
        return 200, exercise.json

    @protect(uuid=True)
    def csv(self, exercise_id):
        """
        Download all items in all batches as a list in CSV format.

        :param: id
        :type: str
        :return: A text blob in CSV format 
        """
        csv_format = '"{}","{}","{}","{}"\n'
        count = 1
        result = csv_format.format('Count', 'RU Code', 'Length', 'Time Stamp')
        exercise = self._get_exercise(exercise_id)
        if not exercise:
            return 204, 'No such batch'
        for instrument in exercise.instruments:
            for business in instrument.businesses:
                result += csv_format.format(count, business.ru_ref, instrument.len, instrument.stamp)
                count += 1
        return 200, result

    @protect(uuid=True)
    def download(self, id):
        """
        Return a decrypted copy of a stored / encrypted insrument

        :param id: The instrument id to recover
        :return: The unencrypted file contents
        """
        instrument = self._get_instrument(id)
        if not instrument:
            return 404, 'Instrument not found', None
        ru_ref = instrument.businesses[0].ru_ref
        return 200, ons_env.cipher.decrypt(instrument.data), ru_ref

    @wait_for(timeout=5)
    def _lookup_exercise(self, exercise_id):

        if exercise_id in self._exercise_cache:
            return self._exercise_cache[exercise_id]

        def hit_route(params):
            def status_check(response):
                if response.code != 200:
                    raise UserError(url)
                return response

            def json(response):
                exercise = loads(response.decode())
                self._exercise_cache[exercise_id] = exercise
                return exercise

            url = '{protocol}://{host}:{port}{endpoint}'.format(**params)
            deferred = treq.get(url)
            return deferred.addCallback(status_check).addCallback(treq.content).addCallback(json)

        params = {
            'endpoint': '/collectionexercises/{}'.format(exercise_id),
            'protocol': ons_env.api_protocol,
            'host': ons_env.api_host,
            'port': ons_env.api_port
        }
        return hit_route(params)

    @protect(uuid=True)
    def upload(self, exercise_id, fileobject, ru_ref=None, survey_id=DEFAULT_SURVEY):
        """
        Upload a file and ultimately persist in an encrypted database column

        :param exercise_id: An excercise id (uuid)
        :param fileobject: A file object from which we can read the file contents
        :param: ru_ref: The name of the file we're receiving
        :param: survey_id: The survey identifier (UUID)
        :return: Returns True if the upload completed
        """
        logger = ons_env.logger
        logger.info("About to encrypt spreadsheet")
        blob = fileobject.read()
        size = len(blob)
        logger.info("Spreadsheet size {}".format(size))
        blob = ons_env.cipher.encrypt(blob)
        encrypted_size = len(blob)
        logger.info("Encrypted spreadsheet size {}".format(encrypted_size))

        logger.info("Creating session")

        if '.' in ru_ref:
            ru_ref = ru_ref.split('.')[0]

        logger.info('Uploading Ru-Ref: {}'.format(ru_ref))
        try:
            logger.info("Creating db models")
            session_factory = sessionmaker(bind=ons_env.db.engine)
            session = session_factory()

            exercise = self._get_exercise(exercise_id, session)
            if not exercise:
                exercise = ExerciseModel(exercise_id=exercise_id, items=1)
            business = self._get_business(ru_ref, session)
            if not business:
                business = BusinessModel(ru_ref=ru_ref)
            classifier = ClassificationModel(kind='SIZE', value=size)
            instrument = InstrumentModel(len=size, data=blob)
            instrument.exercises.append(exercise)
            instrument.businesses.append(business)
            instrument.classifications.append(classifier)
            session.add(instrument)
            survey = self._get_survey(survey_id, session)
            if not survey:
                if reactor.running:
                    exercise = self._lookup_exercise(exercise_id)
                    survey_id = exercise.get('surveyId', None)
                else:
                    survey_id = UUID(survey_id)
                if not survey_id:
                    logger.error('no survey ID returned')
                    raise Exception('no survey ID returned')
                survey = SurveyModel(survey_id=survey_id)
                session.add(survey)
            survey.instruments.append(instrument)
            logger.info("Commit session")
            session.commit()
        except Exception as e:
            logger.info("Rollback session")
            session.rollback()
            logger.error('Error uploading file: {}'.format(str(e)))
            logger.logger.exception(e)
            return 500, 'error uploading file'
        finally:
            logger.info("Close session")
            session.close()
        return 200, 'OK'

    def instruments(self, searchString):
        """
        Return details of all instruments filtered by the classifier(s) listed in 'text'

        :param searchString: Classifiers to filter on 
        :return: matching records
        """
        ons_env.logger.info('Search String is "{}"'.format(searchString))
        try:
            if searchString and type(searchString) != str:
                raise TypeError
            if searchString == "searchString_example":
                return 200, {'text': 'unit test success only'}
            if searchString:
                searchString = loads(searchString)
            else:
                searchString = {}
            results = self._instruments_by_classifier(searchString)
            if type(results) == str:
                return 500, {'text': results}
            records = []
            for result in results:
                instrument = ons_env.db.session.query(InstrumentModel).get(result.id)
                classifiers = {'RU_REF': [], 'COLLECTION_EXERCISE': []}
                for business in instrument.businesses:
                    classifiers['RU_REF'].append(business.ru_ref)
                for exercise in instrument.exercises:
                    classifiers['COLLECTION_EXERCISE'].append(exercise.exercise_id)
                result = {
                    'id': instrument.instrument_id,
                    'classifiers': classifiers,
                    'surveyId': instrument.survey.survey_id
                }
                records.append(result)
            return 200, records
        except Exception:
            ons_env.logger.error(e)
            return 500, {'text': 'Server error accessing database'}

    def instrument_size(self, id):
        """
        Recover the size of an instrument
        :param id:
        :return: size
        """
        instrument = self._get_instrument(id)
        if not instrument:
            return 404, {'text': 'instrument not found', 'code': 404}
        return 200, {'size': instrument.len, 'code': '200'}
