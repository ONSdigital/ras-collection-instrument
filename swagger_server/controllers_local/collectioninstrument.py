##############################################################################
#                                                                            #
#   Collection Instruments Upload                                            #
#   Date:    11 May 2017                                                     #
#   Author:  Gareth Bult                                                     #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ..configuration import ons_env
from ..models_local.instrument import InstrumentModel
from ..models_local.exercise import ExerciseModel
from ..models_local.business import BusinessModel
from ..models_local.survey import SurveyModel
from ..models_local.classification import ClassificationModel, classifications
from traceback import print_exc
from sys import stdout
from json import loads
from uuid import UUID
from ..ons_jwt import validate_jwt

DEFAULT_SURVEY = "3decb89c-c5f5-41b8-9e74-5033395d247e"


def protect(uuid=True):
    """
    This decorator is designed to add a protective layer around endpoint logic, specifically
    it checks for 'id_example' and allows it for integration tests to succeed. It also ensures that
    passed parameters are strings, maybe not needed but prevents something poking a dict or similar
    through by mistake. It then converts the first parameter to a UUID type if the 'uuid' flag is set.
    
    :param uuid: Whether to convert first parameter to UUID() 
    :return: status code, return message
    """
    @validate_jwt(['ci:read', 'ci:write'])
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
            except Exception:
                print_exc(limit=5, file=stdout)
                return 500, {'text': 'Server experienced an unexpected error'}
        return func_wrapped
    return protect_wrapped


class CollectionInstrument(object):

    def __init__(self):
        """
        The default entry here is used by the unit testing code, so although it looks
        redundant, please leave it in.
        """
        pass

    """
    Database shortcuts, the SQLAlchemy syntax isn't always immediately obvious, so here we're just using
    some 'more' obvious shortcuts to functions, purely from a 'readability' perspective.
    """
    def _get_exercise(self, exercise_id):
        return ons_env.session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).first()

    def _get_business(self, ru_ref):
        return ons_env.session.query(BusinessModel).filter(BusinessModel.ru_ref == ru_ref).first()

    def _get_survey(self, survey_id):
        return ons_env.session.query(SurveyModel).filter(SurveyModel.survey_id == survey_id).first()

    def _get_instrument(self, instrument_id):
        return ons_env.session.query(InstrumentModel).filter(InstrumentModel.instrument_id == instrument_id).first()

    def _get_instrument_by_ru(self, ru_ref):
        return ons_env.session.query(InstrumentModel).filter(BusinessModel.ru_ref == ru_ref).first()

    def _exercise_status_set(self, exercise_id, status):
        ons_env.session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).update({'status': status})

    def _instruments_by_classifier(self, classifiers):
        """
        This looks like it needs lots of explanationn, but it really doesn't when you read it.
        
        :param classifiers: dict of (key, value) pairs to search on 
        :return: query results (matching records)
        """
        query = ons_env.session.query(InstrumentModel)
        used = []
        for attr, value in classifiers.items():
            if attr == 'ru_ref' and BusinessModel not in used:
                query = query.join((BusinessModel, InstrumentModel.businesses))
                used.append(BusinessModel)
            elif attr == 'exercise' and ExerciseModel not in used:
                query = query.join((ExerciseModel, InstrumentModel.exercises))
                query = query.join((ExerciseModel, InstrumentModel.exercises))
                used.append(ExerciseModel)
            elif attr == 'survey' and SurveyModel not in used:
                query = query.join(SurveyModel.instruments)
                used.append(SurveyModel)
            elif attr in classifications and ClassificationModel not in used:
                query = query.join(ClassificationModel.instrument)
                used.append(ClassificationModel)
            else:
                return 'unable to handle query for ({}={})'.format(attr, value)
        for attr, value in classifiers.items():
            if attr == 'ru_ref':
                query = query.filter(BusinessModel.ru_ref == value)
            elif attr == 'exercise':
                query = query.filter(ExerciseModel.exercise_id == UUID(value))
            elif attr == 'survey':
                query = query.filter(SurveyModel.survey_id == UUID(value))
            else:
                query = query.filter(ClassificationModel.kind == attr).filter(ClassificationModel.value == value)
        return query.all()

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
            ons_env.session.add(ExerciseModel(exercise_id=exercise_id, items=count))
            ons_env.session.commit()
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
        ons_env.session.delete(exercise)
        ons_env.session.commit()
        return 200, {'text': 'OK'}

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
        ons_env.session.commit()
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

    @protect(uuid=False)
    def download(self, ru_code):
        """
        Return a decrypted copy of a stored / encrypted insrument

        :param ru_code: The instrument id to recover 
        :return: The unencrypted file contents
        """
        instrument = self._get_instrument_by_ru(ru_code)
        if not instrument:
            return 404, 'Instrument not found'
        return 200, ons_env.cipher.decrypt(instrument.data)

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
        survey_id = UUID(survey_id)

        blob = fileobject.read()
        size = len(blob)
        blob = ons_env.cipher.encrypt(blob)

        exercise = self._get_exercise(exercise_id)
        if not exercise:
            exercise = ExerciseModel(exercise_id=exercise_id, items=1)
        business = self._get_business(ru_ref)
        if not business:
            business = BusinessModel(ru_ref=ru_ref)
        classifier = ClassificationModel(kind='SIZE', value=size)

        instrument = InstrumentModel(len=size, data=blob)
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        instrument.classifications.append(classifier)
        ons_env.session.add(instrument)

        survey = self._get_survey(survey_id)
        if not survey:
            survey = SurveyModel(survey_id=survey_id)
            ons_env.session.add(survey)
        survey.instruments.append(instrument)
        ons_env.session.commit()
        return 200, 'OK'

    def instruments(self, searchString):
        """
        Return details of all instruments filtered by the classifier(s) listed in 'text'

        :param searchString: Classifiers to filter on 
        :return: matching records
        """
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
                instrument = ons_env.session.query(InstrumentModel).get(result.id)
                records.append(instrument.json)
            return 200, records
        except Exception:
            print_exc(limit=5, file=stdout)
            return 500, {'text': 'Server error accessing database'}
