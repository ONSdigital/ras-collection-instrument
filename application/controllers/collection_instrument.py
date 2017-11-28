from application.controllers.cryptographer import Cryptographer
from application.controllers.helper import validate_uuid
from application.controllers.service_request import service_request
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import query_business_by_ru, query_exercise_by_id, query_instrument, \
    query_instrument_by_id, query_survey_by_id
from application.models.models import BusinessModel, ClassificationModel, ExerciseModel, InstrumentModel, SurveyModel
from json import loads
from ras_common_utils.ras_error.ras_error import RasError
from structlog import get_logger


log = get_logger()

UPLOAD_SUCCESSFUL = 'The upload was successful'
COLLECTION_EXERCISE_NOT_FOUND = 'Collection exercise not found'
COLLECTION_INSTRUMENT_NOT_FOUND = 'Collection instrument not found'
INVALID_CLASSIFIER = "{} is an invalid classifier, you can't search on it"
DEFAULT_SURVEY_ID = 'cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87'


class CollectionInstrument(object):

    @with_db_session
    def get_instrument_by_search_string(self, search_string=None, session=None):
        """
        Get Instrument from the db using the search string passed
        :param search_string: Classifiers to filter on
        :param session: database session
        :return: matching records
        """

        log.info('Searching for instrument using search string: "{}"'.format(search_string))

        if search_string:
            json_search_parameters = loads(search_string)
        else:
            json_search_parameters = {}

        results = self._get_instruments_by_classifier(json_search_parameters, session)

        records = []
        for result in results:
            instrument = session.query(InstrumentModel).get(result.id)
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

    @staticmethod
    @with_db_session
    def upload_instrument(exercise_id, ru_ref, file, survey_id=DEFAULT_SURVEY_ID, session=None):
        """
        Encrypt and upload a collection instrument to the db
        :param exercise_id: An exercise id (UUID)
        :param ru_ref: The name of the file we're receiving
        :param file: A file object from which we can read the file contents
        :param survey_id: The survey identifier (UUID)
        :param session: database session
        :return Returns 'UPLOAD_SUCCESSFUL' if the upload completed
        """

        log.info('Upload Ru-Ref: {}'.format(ru_ref))

        validate_uuid([exercise_id, survey_id])

        file_contents = file.read()
        file_size = len(file_contents)
        classifier = ClassificationModel(kind='SIZE', value=file_size)

        exercise = query_exercise_by_id(exercise_id, session)
        if not exercise:
            exercise = ExerciseModel(exercise_id=exercise_id, items=1)

        business = query_business_by_ru(ru_ref, session)
        if not business:
            business = BusinessModel(ru_ref=ru_ref)

        cryptographer = Cryptographer()
        encrypted_file = cryptographer.encrypt(file_contents)
        instrument = InstrumentModel(length=file_size, data=encrypted_file)
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        instrument.classifications.append(classifier)

        survey = query_survey_by_id(survey_id, session)

        if not survey:
            response = service_request(service='collectionexercise-service',
                                       endpoint='collectionexercises',
                                       search_value=exercise_id)
            survey_id = response.json().get('surveyId')
            survey = SurveyModel(survey_id=survey_id)
            session.add(survey)

        instrument.survey = survey
        session.add(instrument)

        return 200, UPLOAD_SUCCESSFUL

    @staticmethod
    @with_db_session
    def get_instruments_by_exercise_id_csv(exercise_id, session=None):
        """
        Finds all collection instruments associated with an exercise and returns them in csv format
        :param exercise_id
        :param session: database session
        :return: collection instruments in csv
        """
        log.info('Getting csv for instruments using exercise id {}'.format(exercise_id))

        validate_uuid([exercise_id])
        csv_format = '"{count}","{ru_ref}","{length}","{date_stamp}"\n'
        count = 1
        result = csv_format.format(count='Count',
                                   ru_ref='RU Code',
                                   length='Length',
                                   date_stamp='Time Stamp')
        exercise = query_exercise_by_id(exercise_id, session)

        if not exercise:
            return 404, COLLECTION_EXERCISE_NOT_FOUND

        for instrument in exercise.instruments:
            for business in instrument.businesses:
                result += csv_format.format(count=count,
                                            ru_ref=business.ru_ref,
                                            length=instrument.len,
                                            date_stamp=instrument.stamp)
                count += 1
        return 200, result

    @staticmethod
    @with_db_session
    def get_instrument_by_id(instrument_id, session=None):
        """
        Get collection instrument from the db using the id
        :param instrument_id: The id of the instrument we want
        :param session: database session
        :return: formatted JSON version of the instrument
        """

        log.info('Searching for instrument using id {}'.format(instrument_id))

        validate_uuid([instrument_id])

        instrument = query_instrument_by_id(instrument_id, session)
        if not instrument:
            return 404, COLLECTION_INSTRUMENT_NOT_FOUND
        return 200, instrument.json

    def _get_instruments_by_classifier(self, json_search_parameters, session):
        """
        Search collection instrument by classifiers.
        :param json_search_parameters: dict of (key, value) pairs to search on
        :param session: database session
        :return: query results
        """

        query = self._build_model_joins(json_search_parameters, session)

        for classifier, value in json_search_parameters.items():
            if classifier == 'RU_REF':
                query = query.filter(BusinessModel.ru_ref == value)
            elif classifier == 'COLLECTION_EXERCISE':
                query = query.filter(ExerciseModel.exercise_id == value)
            elif classifier == 'SURVEY_ID':
                query = query.filter(SurveyModel.survey_id == value)
        return query.all()

    @staticmethod
    def _build_model_joins(json_search_parameters, session):
        """
        Builds the model joins needed for a search
        :param json_search_parameters: dict of (key, value) pairs to join on
        :param session: database session
        :return: query results
        """
        log.info('creating model joins for search')

        query = query_instrument(session)
        already_joined = []
        for classifier in json_search_parameters.keys():
            if classifier == 'RU_REF' and BusinessModel not in already_joined:
                query = query.join((BusinessModel, InstrumentModel.businesses))
                already_joined.append(BusinessModel)

            elif classifier == 'COLLECTION_EXERCISE' and ExerciseModel not in already_joined:
                query = query.join((ExerciseModel, InstrumentModel.exercises))
                already_joined.append(ExerciseModel)

            elif classifier == 'SURVEY_ID' and SurveyModel not in already_joined:
                query = query.join(SurveyModel, InstrumentModel.survey)
                already_joined.append(SurveyModel)
            else:
                raise RasError(INVALID_CLASSIFIER.format(classifier), 500)

        return query
