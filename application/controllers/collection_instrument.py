import logging
import structlog

from application.controllers.cryptographer import Cryptographer
from application.controllers.helper import validate_uuid
from application.controllers.service_helper import service_request
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import query_business_by_ru, query_exercise_by_id, query_instrument, \
    query_instrument_by_id, query_survey_by_id
from application.exceptions import RasError
from application.models.models import BusinessModel, ClassificationModel, ExerciseModel, InstrumentModel, SurveyModel
from json import loads

log = structlog.wrap_logger(logging.getLogger(__name__))

UPLOAD_SUCCESSFUL = 'The upload was successful'
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
        instruments = []
        for result in results:
            query = session.query(InstrumentModel).get(result.id)
            classifiers = {'RU_REF': [], 'COLLECTION_EXERCISE': []}
            for business in query.businesses:
                classifiers['RU_REF'].append(business.ru_ref)
            for exercise in query.exercises:
                classifiers['COLLECTION_EXERCISE'].append(exercise.exercise_id)
            result = {
                'id': query.instrument_id,
                'classifiers': classifiers,
                'surveyId': query.survey.survey_id
            }
            instruments.append(result)
        return instruments

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
        return UPLOAD_SUCCESSFUL

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
        csv = csv_format.format(count='Count',
                                ru_ref='RU Code',
                                length='Length',
                                date_stamp='Time Stamp')
        exercise = query_exercise_by_id(exercise_id, session)

        if not exercise:
            return None

        for instrument in exercise.instruments:
            for business in instrument.businesses:
                csv += csv_format.format(count=count,
                                         ru_ref=business.ru_ref,
                                         length=instrument.len,
                                         date_stamp=instrument.stamp)
                count += 1
        return csv

    @staticmethod
    @with_db_session
    def get_instrument_json(instrument_id, session):
        """
        Get collection instrument json from the db
        :param instrument_id: The id of the instrument we want
        :return: formatted JSON version of the instrument
        """

        instrument = CollectionInstrument.get_instrument_by_id(instrument_id, session)
        instrument_json = instrument.json if instrument else None
        return instrument_json

    @staticmethod
    @with_db_session
    def get_instrument_data(instrument_id, session):
        """
        Get the instrument data from the db using the id
        :param instrument_id: The id of the instrument we want
        :return: data and ru_ref
        """

        instrument = CollectionInstrument.get_instrument_by_id(instrument_id, session)

        data = None
        ru_ref = None
        if instrument:
            log.info('Decrypting collection instrument data for {}'.format(instrument_id))
            cryptographer = Cryptographer()
            data = cryptographer.decrypt(instrument.data)
            ru_ref = instrument.businesses[0].ru_ref
        return data, ru_ref

    @staticmethod
    def get_instrument_by_id(instrument_id, session):
        """
        Get the collection instrument from the db using the id
        :param instrument_id: The id of the instrument we want
        :return: instrument
        """
        log.info('Searching for instrument using id {}'.format(instrument_id))
        validate_uuid([instrument_id])
        instrument = query_instrument_by_id(instrument_id, session)
        return instrument

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
