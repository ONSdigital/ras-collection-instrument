import logging
import uuid
from json import dumps, loads

import structlog

from application.controllers.cryptographer import Cryptographer
from application.controllers.helper import validate_uuid
from application.controllers.rabbit_helper import initialise_rabbitmq_exchange, send_message_to_rabbitmq_exchange
from application.controllers.service_helper import service_request
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import query_business_by_ru, query_exercise_by_id, query_instrument, \
    query_instrument_by_id, query_survey_by_id
from application.exceptions import RasError
from application.models.models import BusinessModel, ExerciseModel, InstrumentModel, SurveyModel, SEFTModel

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
                'file_name': instrument.name,
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
        :return: a collection instrument instance
        """

        log.info('Upload exercise', exercise_id=exercise_id)

        validate_uuid(exercise_id)
        instrument = InstrumentModel(ci_type='SEFT')

        seft_file = self._create_seft_file(instrument.instrument_id, file)
        instrument.seft_file = seft_file

        exercise = self._find_or_create_exercise(exercise_id, session)
        instrument.exercises.append(exercise)

        survey = self._find_or_create_survey_from_exercise_id(exercise_id, session)
        instrument.survey = survey

        if ru_ref:
            business = self._find_or_create_business(ru_ref, session)
            self.validate_one_instrument_for_ru_specific_upload(exercise, business, session)
            instrument.businesses.append(business)

        if classifiers:
            instrument.classifiers = loads(classifiers)

        session.add(instrument)
        return instrument

    @with_db_session
    def patch_seft_instrument(self, instrument_id: str, file, session):

        instrument = self.get_instrument_by_id(instrument_id, session)
        if instrument is None:
            log.error('Instrument not found')
            raise RasError('Instrument not found', 400)
        if instrument.type != 'SEFT':
            log.error('Not a SEFT instrument')
            raise RasError('Not a SEFT instrument', 400)

        seft_model = self._update_seft_file(instrument.seft_file, file)
        session.add(seft_model)

    @staticmethod
    def validate_one_instrument_for_ru_specific_upload(exercise, business, session):
        """
        Checks there hasn't been an instrument loaded for this reporting unit in this collection exercise already.

        The algorithm for this is as follows:
          - Check if this business_id is related to other instrument_id's.
          - If true, check each the exercise_id for each of those instruments to see if it matches the exercise we're
          attempting to add to.
          - If any match, then we're trying to add a second collection instrument for a reporting unit for this
          collection exercise and an exception will be raised.

        :param exercise: A db object representing the collection exercise
        :param business: A db object representing the business data
        :param session: A database session
        :raises RasError:  Raised when a duplicate is found

        """
        bound_logger = log.bind(ru_ref=business.ru_ref)
        bound_logger.info("Validating only one instrument per reporting unit per exercise")
        business = query_business_by_ru(business.ru_ref, session)
        if business:
            business_id = str(business.id)
            for instrument in business.instruments:
                instrument_id = str(instrument.id)
                bound_logger.bind(id_of_instrument=instrument_id, business_id=business_id)
                bound_logger.info('Reporting unit has had collection instruments uploaded for it in the past')

                for related_exercise in instrument.exercises:
                    related_exercise_id = related_exercise.exercise_id
                    exercise_id = exercise.exercise_id
                    bound_logger.bind(exercise_id=exercise_id, related_exercise_id=related_exercise_id)
                    bound_logger.info("About to check exercise for match")
                    if related_exercise_id == exercise_id:
                        bound_logger.info('Was about to add a second instrument for a reporting unit for a '
                                          'collection exercise')
                        ru_ref = business.ru_ref
                        error_text = f'Reporting unit {ru_ref} already has an instrument ' \
                                     f'uploaded for this collection exercise'
                        raise RasError(error_text, 400)

    @with_db_session
    def upload_instrument_with_no_collection_exercise(self, survey_id, classifiers=None, session=None):
        """
        Upload a collection instrument to the db without a collection exercise

        :param classifiers: Classifiers associated with the instrument
        :param session: database session
        :param survey_id: database session
        :return: a collection instrument instance
        """

        log.info('Upload instrument', survey_id=survey_id)

        validate_uuid(survey_id)
        instrument = InstrumentModel(ci_type='EQ')

        survey = self._find_or_create_survey_from_survey_id(survey_id, session)
        instrument.survey = survey

        if classifiers:
            deserialized_classifiers = loads(classifiers)
            instruments = self._get_instruments_by_classifier(deserialized_classifiers, None, session)
            for instrument in instruments:
                if instrument.classifiers == deserialized_classifiers:
                    raise RasError("Cannot upload an instrument with an identical set of classifiers", 400)
            instrument.classifiers = deserialized_classifiers

        session.add(instrument)

        return instrument

    @with_db_session
    def link_instrument_to_exercise(self, instrument_id, exercise_id, session=None):
        """
        Link a collection instrument to a collection exercise

        :param instrument_id: A collection instrument id (UUID)
        :param exercise_id: A collection exercise id (UUID)
        :param session: database session
        :return: True if instrument has been successfully linked to exercise
        """
        log.info('Linking instrument to exercise', instrument_id=instrument_id, exercise_id=exercise_id)
        validate_uuid(instrument_id)
        validate_uuid(exercise_id)

        instrument = self.get_instrument_by_id(instrument_id, session)
        exercise = self._find_or_create_exercise(exercise_id, session)
        instrument.exercises.append(exercise)

        log.info('Successfully linked instrument to exercise', instrument_id=instrument_id, exercise_id=exercise_id)
        return True

    @with_db_session
    def unlink_instrument_from_exercise(self, instrument_id, exercise_id, session=None):
        """
        Unlink a collection instrument and a collection exercise.  If there is a link between the exercise
        and a business, this will also be removed.

        :param instrument_id: A collection instrument id (UUID)
        :param exercise_id: A collection exercise id (UUID)
        :param session: database session
        :return: True if instrument has been successfully unlinked to exercise
        """
        bound_logger = log.bind(instrument_id=instrument_id, exercise_id=exercise_id)
        bound_logger.info('Unlinking instrument and exercise')

        instrument = self.get_instrument_by_id(instrument_id, session)
        exercise = self.get_exercise_by_id(exercise_id, session)
        if not instrument or not exercise:
            bound_logger.info('Failed to unlink, unable to find instrument or exercise')
            raise RasError('Unable to find instrument or exercise', 404)

        instrument.exercises.remove(exercise)
        for business in instrument.businesses:
            bound_logger.info("Removing business/exercise link", business_id=business.id, ru_ref=business.ru_ref)
            business.instruments.remove(instrument)

        if not self.publish_remove_collection_instrument(exercise_id, instrument.instrument_id):
            raise RasError('Failed to publish upload message', 500)

        bound_logger.info('Successfully unlinked instrument to exercise')
        return True

    @staticmethod
    def initialise_messaging():
        log.info('Initialising rabbitmq exchange for Collection Instruments', queue=RABBIT_QUEUE_NAME)
        initialise_rabbitmq_exchange(RABBIT_QUEUE_NAME)

    @staticmethod
    def publish_remove_collection_instrument(exercise_id, instrument_id):
        """
        Publish message to a rabbitmq exchange with details of collection exercise and instrument unlinked

        :param exercise_id: An exercise id (UUID)
        :param instrument_id: The id (UUID) of collection instrument
        :return: True if message successfully published to RABBIT_QUEUE_NAME
        """
        log.info('Publishing remove message', exercise_id=exercise_id, instrument_id=instrument_id)

        tx_id = str(uuid.uuid4())
        json_message = dumps({
            'action': 'REMOVE',
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
        :return: A survey record
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
    def _find_or_create_survey_from_survey_id(survey_id, session):
        """
        reuses the survey if it exists in this service or create if it doesn't

        :param survey_id: A survey id (UUID)
        :param session: database session
        :return: A survey record
        """

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
        :return: exercise
        """

        exercise = query_exercise_by_id(exercise_id, session)
        if not exercise:
            log.info('creating exercise', exercise_id=exercise_id)
            exercise = ExerciseModel(exercise_id=exercise_id, items=1)
        return exercise

    @staticmethod
    def get_exercise_by_id(exercise_id, session):
        """
        Retrieves exercise

        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return: exercise
        """
        log.info('Searching for exercise', exercise_id=exercise_id)
        validate_uuid(exercise_id)
        exercise = query_exercise_by_id(exercise_id, session)
        return exercise

    @staticmethod
    def _find_or_create_business(ru_ref, session):
        """
        Creates a business in the db if it doesn't exist, or reuses if it does

        :param ru_ref: The name of the file we're receiving
        :param session: database session
        :return:  business
        """
        business = query_business_by_ru(ru_ref, session)
        if not business:
            log.info('creating business', ru_ref=ru_ref)
            business = BusinessModel(ru_ref=ru_ref)
        return business

    @staticmethod
    def _create_seft_file(instrument_id, file):
        """
        Creates a seft_file with an encrypted version of the file

        :param file: A file object from which we can read the file contents
        :return: instrument
        """
        log.info('creating instrument seft file')
        file_contents = file.read()
        file_size = len(file_contents)
        cryptographer = Cryptographer()
        encrypted_file = cryptographer.encrypt(file_contents)
        seft_file = SEFTModel(instrument_id=instrument_id, file_name=file.filename,
                              length=file_size, data=encrypted_file)
        return seft_file

    @staticmethod
    def _update_seft_file(seft_model, file):
        """
        Updates a seft_file with a new version of the data

        :param file: A file object from which we can read the file contents
        :return: instrument
        """
        log.info('Updating instrument seft file')
        file_contents = file.read()
        file_size = len(file_contents)
        cryptographer = Cryptographer()
        encrypted_file = cryptographer.encrypt(file_contents)
        seft_model.data = encrypted_file
        seft_model.length = file_size
        seft_model.file_name = file.filename
        return seft_model

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
                                     file_name=instrument.name,
                                     length=instrument.seft_file.len if instrument.seft_file else None,
                                     date_stamp=instrument.stamp)
            count += 1
        return csv

    @staticmethod
    @with_db_session
    def get_instrument_json(instrument_id, session):
        """
        Get collection instrument json from the db

        :param instrument_id: The id of the instrument we want
        :param session: database session
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
        :param session: database session
        :return: data and file_name
        """

        instrument = CollectionInstrument.get_instrument_by_id(instrument_id, session)

        data = None
        file_name = None
        if instrument:
            log.info('Decrypting collection instrument data', instrument_id=instrument_id)
            cryptographer = Cryptographer()
            data = cryptographer.decrypt(instrument.seft_file.data)
            file_name = instrument.seft_file.file_name
        return data, file_name

    @staticmethod
    def get_instrument_by_id(instrument_id, session):
        """
        Get the collection instrument from the db using the id

        :param instrument_id: The id of the instrument we want
        :param session: database session
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
            elif classifier == 'TYPE':
                query = query.filter(InstrumentModel.type == value)
            else:
                query = query.filter(InstrumentModel.classifiers.contains({classifier.lower(): value}))
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
