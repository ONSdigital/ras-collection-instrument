import logging
import structlog
import uuid

from json import dumps, loads
from application.controllers.cryptographer import Cryptographer
from application.controllers.helper import validate_uuid
from application.controllers.rabbit_helper import initialise_rabbitmq_exchange, send_message_to_rabbitmq_exchange
from application.controllers.service_helper import service_request
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import query_business_by_ru, query_exercise_by_id, query_instrument, \
    query_instrument_by_id, query_survey_by_id
from application.exceptions import RasError
from application.models.models import BusinessModel, ExerciseModel, InstrumentModel, SurveyModel


log = structlog.wrap_logger(logging.getLogger(__name__))

RABBIT_QUEUE_NAME = 'Seft.Instruments'


class CollectionInstrument(object):

    @with_db_session
    def get_instrument_by_search_string(self, search_string=None, limit=None, session=None):
        """
        Get Instrument from the db using the search string passed
        :param search_string: Classifiers to filter on
        :param limit: the amount of records to return
        :param session: database session
        :return: matching records
        """

        log.info('Searching for instrument', search_string=search_string)

        if search_string:
            json_search_parameters = loads(search_string)
        else:
            json_search_parameters = {}

        instruments = self._get_instruments_by_classifier(json_search_parameters, limit, session)

        result = []
        for instrument in instruments:

            classifiers = instrument.classifiers or {}
            ru = {'RU_REF': []}
            collection_exercise = {'COLLECTION_EXERCISE': []}

            for business in instrument.businesses:
                ru['RU_REF'].append(business.ru_ref)

            for exercise in instrument.exercises:
                collection_exercise['COLLECTION_EXERCISE'].append(exercise.exercise_id)

            instrument_json = {
                'id': instrument.instrument_id,
                'file_name': instrument.file_name,
                'classifiers': {**classifiers, **ru, **collection_exercise},
                'surveyId': instrument.survey.survey_id
            }
            result.append(instrument_json)
        return result

    @with_db_session
    def upload_instrument(self, exercise_id, file, ru_ref=None, classifiers=None, session=None):
        """
        Encrypt and upload a collection instrument to the db
        :param exercise_id: An exercise id (UUID)
        :param ru_ref: The name of the file we're receiving
        :param classifiers: Classifiers associated with the instrument
        :param file: A file object from which we can read the file contents
        :param session: database session
        :return a collection instrument instance
        """

        log.info('Upload exercise', exercise_id=exercise_id)

        validate_uuid(exercise_id)
        instrument = self._create_instrument(file)

        exercise = self._find_or_create_exercise(exercise_id, session)
        instrument.exercises.append(exercise)

        survey = self._find_or_create_survey_from_exercise_id(exercise_id, session)
        instrument.survey = survey

        if ru_ref:
            business = self._find_or_create_business(ru_ref, session)
            instrument.businesses.append(business)

        if classifiers:
            instrument.classifiers = loads(classifiers)

        session.add(instrument)
        if not self.publish_uploaded_collection_instrument(exercise_id, instrument.instrument_id):
            raise RasError('Failed to publish upload message', 500)
        return instrument

    @with_db_session
    def upload_instrument_with_no_collection_exercise(self, classifiers=None, session=None):
        """
        Encrypt and upload a collection instrument to the db
        :param classifiers: Classifiers associated with the instrument
        :param session: database session
        :return a collection instrument instance
        """

        instrument = self._create_instrument()

        survey = self._find_or_create_survey_from_exercise_id(session)
        instrument.survey = survey

        if classifiers:
            instrument.classifiers = loads(classifiers)

        session.add(instrument)
        if not self.publish_uploaded_collection_instrument(instrument.instrument_id):
            raise RasError('Failed to publish upload message', 500)
        return instrument

    @staticmethod
    def initialise_messaging():
        log.info('Initialising rabbitmq exchange for Collection Instruments', queue=RABBIT_QUEUE_NAME)
        initialise_rabbitmq_exchange(RABBIT_QUEUE_NAME)

    @staticmethod
    def publish_uploaded_collection_instrument(exercise_id, instrument_id):
        """
        Publish message to a rabbitmq exchange with details of collection exercise and instrument
        :param exercise_id: An exercise id (UUID)
        :param instrument_id: The id (UUID) for the newly created collection instrument
        :return True if message successfully published to RABBIT_QUEUE_NAME
        """
        log.info('Publishing upload message', exercise_id=exercise_id, instrument_id=instrument_id)

        tx_id = str(uuid.uuid4())
        json_message = dumps({
            'action': 'ADD',
            'exercise_id': str(exercise_id),
            'instrument_id': str(instrument_id)
        })
        return send_message_to_rabbitmq_exchange(json_message, tx_id, RABBIT_QUEUE_NAME, encrypt=False)

    @staticmethod
    def _find_or_create_survey_from_exercise_id(exercise_id, session):
        """
        Makes a request to the collection exercise service for the survey ID,
        reuses the survey if it exists in this service or create if it doesn't
        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return survey
        """
        response = service_request(service='collectionexercise-service',
                                   endpoint='collectionexercises',
                                   search_value=exercise_id)
        survey_id = response.json().get('surveyId')

        survey = query_survey_by_id(survey_id, session)
        if not survey:
            log.info('creating survey', survey_id=survey_id)
            survey = SurveyModel(survey_id=survey_id)
        return survey

    @staticmethod
    def _find_or_create_exercise(exercise_id, session):
        """
        Creates a exercise in the db if it doesn't exist, or reuses if it does
        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return exercise
        """

        exercise = query_exercise_by_id(exercise_id, session)
        if not exercise:
            log.info('creating exercise', exercise_id=exercise_id)
            exercise = ExerciseModel(exercise_id=exercise_id, items=1)
        return exercise

    @staticmethod
    def _find_or_create_business(ru_ref, session):
        """
        Creates a business in the db if it doesn't exist, or reuses if it does
        :param ru_ref: The name of the file we're receiving
        :param session: database session
        :return  business
        """
        business = query_business_by_ru(ru_ref, session)
        if not business:
            log.info('creating business', ru_ref=ru_ref)
            business = BusinessModel(ru_ref=ru_ref)
        return business

    @staticmethod
    def _create_instrument(file):
        """
        Creates a Instrument with an encrypted version of the file
        :param file: A file object from which we can read the file contents
        :return instrument
        """
        log.info('creating instrument')
        file_contents = file.read()
        file_size = len(file_contents)
        cryptographer = Cryptographer()
        encrypted_file = cryptographer.encrypt(file_contents)
        instrument = InstrumentModel(file_name=file.filename, length=file_size, data=encrypted_file)
        return instrument

    @staticmethod
    @with_db_session
    def get_instruments_by_exercise_id_csv(exercise_id, session=None):
        """
        Finds all collection instruments associated with an exercise and returns them in csv format
        :param exercise_id
        :param session: database session
        :return: collection instruments in csv
        """
        log.info('Getting csv for instruments', exercise_id=exercise_id)

        validate_uuid(exercise_id)
        csv_format = '"{count}","{file_name}","{length}","{date_stamp}"\n'
        count = 1
        csv = csv_format.format(count='Count',
                                file_name='File Name',
                                length='Length',
                                date_stamp='Time Stamp')
        exercise = query_exercise_by_id(exercise_id, session)

        if not exercise:
            return None

        for instrument in exercise.instruments:
            csv += csv_format.format(count=count,
                                     file_name=instrument.file_name,
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
        :return: data and file_name
        """

        instrument = CollectionInstrument.get_instrument_by_id(instrument_id, session)

        data = None
        file_name = None
        if instrument:
            log.info('Decrypting collection instrument data', instrument_id=instrument_id)
            cryptographer = Cryptographer()
            data = cryptographer.decrypt(instrument.data)
            file_name = instrument.file_name
        return data, file_name

    @staticmethod
    def get_instrument_by_id(instrument_id, session):
        """
        Get the collection instrument from the db using the id
        :param instrument_id: The id of the instrument we want
        :return: instrument
        """
        log.info('Searching for instrument', instrument_id=instrument_id)
        validate_uuid(instrument_id)
        instrument = query_instrument_by_id(instrument_id, session)
        return instrument

    def _get_instruments_by_classifier(self, json_search_parameters, limit, session):
        """
        Search collection instrument by classifiers.
        :param json_search_parameters: dict of (key, value) pairs to search on
        :param limit: the amount of records to return
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
            else:
                query = query.filter(InstrumentModel.classifiers.contains({classifier: value}))
        result = query.order_by(InstrumentModel.stamp.desc())

        if limit:
            return result.limit(limit)
        return result.all()

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
        return query
