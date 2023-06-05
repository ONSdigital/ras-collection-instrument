import logging
from json import loads

import structlog
from flask import current_app
from sqlalchemy.orm import Session

from application.controllers.helper import validate_uuid
from application.controllers.service_helper import get_survey_details, service_request
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import (
    query_business_by_ru,
    query_exercise_by_id,
    query_instrument,
    query_instrument_by_id,
    query_instruments_form_type_with_different_survey_mode,
    query_survey_by_id,
)
from application.exceptions import GCPBucketException, RasError
from application.models.google_cloud_bucket import GoogleCloudSEFTCIBucket
from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
    SEFTModel,
    SurveyModel,
)

log = structlog.wrap_logger(logging.getLogger(__name__))

COLLECTION_EXERCISE_NOT_FOUND_IN_DB = "Collection exercise not found in database"
COLLECTION_EXERCISE_NOT_FOUND_ON_GCP = "Collection exercise not found on GCP"
COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED = (
    "Collection exercise and instruments successfully deleted from database and GCP (if applicable)"
)


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

        log.info("Searching for instrument", search_string=search_string)

        if search_string:
            json_search_parameters = loads(search_string)
        else:
            json_search_parameters = {}

        instruments = self._get_instruments_by_classifier(json_search_parameters, limit, session)

        result = []
        for instrument in instruments:
            classifiers = instrument.classifiers or {}

            # Leaving these as empty lists for now. Before it would loop over the instrument.businesses and
            # instrument.exercises and populate the lists.  We're almost certain nothing uses this, or the 'classifiers'
            # key in the instrument_json at all.  If this proves to be the case after we deploy this change then we can
            # fully remove it in a future PR
            ru = {"RU_REF": []}
            collection_exercise = {"COLLECTION_EXERCISE": []}

            instrument_json = {
                "id": instrument.instrument_id,
                "file_name": instrument.name,
                "type": instrument.type,
                "classifiers": {**classifiers, **ru, **collection_exercise},
                "surveyId": instrument.survey.survey_id,
            }
            result.append(instrument_json)
        return result

    @with_db_session
    def upload_seft_to_bucket(self, exercise_id, file, ru_ref=None, classifiers=None, session=None):
        """
        Encrypt and upload a SEFT collection instrument to the bucket and db

        :param exercise_id: An exercise id (UUID)
        :param ru_ref: The name of the file we're receiving
        :param classifiers: Classifiers associated with the instrument
        :param file: A file object from which we can read the file contents
        :param session: database session
        :return: a collection instrument instance
        """
        log.info("Upload instrument", exercise_id=exercise_id)

        validate_uuid(exercise_id)
        self.validate_non_duplicate_instrument(file, exercise_id, session)

        survey = self._find_or_create_survey_from_exercise_id(exercise_id, session)
        survey_id = survey.survey_id
        survey_service_details = get_survey_details(survey_id)
        if survey_service_details["surveyMode"] == "EQ_AND_SEFT" and ru_ref is not None:
            raise RasError("Can't upload a reporting unit specific instrument for an EQ_AND_SEFT survey", 400)

        ci_type = "SEFT"
        instrument = InstrumentModel(ci_type=ci_type)
        if classifiers:
            classifiers = loads(classifiers)
            if survey_service_details["surveyMode"] == "EQ_AND_SEFT":
                self.validate_eq_and_seft_form_type(survey_id, classifiers.get("form_type"), ci_type, session)
            instrument.classifiers = classifiers

        exercise = self._find_or_create_exercise(exercise_id, session)
        if ru_ref:
            business = self._find_or_create_business(ru_ref, session)
            self.validate_one_instrument_for_ru_specific_upload(exercise, business, session)
            instrument.businesses.append(business)

        seft_file = self._create_seft_file(instrument.instrument_id, file)
        instrument.seft_file = seft_file
        instrument.exercises.append(exercise)
        instrument.survey = survey
        session.add(instrument)

        try:
            file.filename = survey_service_details["surveyRef"] + "/" + exercise_id + "/" + file.filename
            seft_ci_bucket = GoogleCloudSEFTCIBucket(current_app.config)
            seft_ci_bucket.upload_file_to_bucket(file=file)
        except Exception as e:
            log.exception("An error occurred when trying to put SEFT CI in bucket")
            raise e

        return instrument

    @staticmethod
    def validate_eq_and_seft_form_type(survey_id: str, form_type: str, survey_mode: str, session: Session) -> None:
        """
        Validates when using EQ_AND_SEFT that there isn't a different survey mode already using the form type
        uploaded in the same survey
        :param survey_id: survey id
        :param form_type: form type (i.e 0001)
        :param survey_mode: survey mode (i.e SEFT)
        :param session: session
        :return: None
        """
        instruments = query_instruments_form_type_with_different_survey_mode(survey_id, form_type, survey_mode, session)
        if instruments:
            instrument_type = instruments[0].type
            log.info(
                "Instrument can not be uploaded, a different survey mode already uses this form_type",
                survey_id=survey_id,
                form_type=form_type,
                instrument_type=instrument_type,
            )
            raise RasError(f"This form type is currently being used by {instrument_type} for this survey", 400)

    @staticmethod
    def validate_non_duplicate_instrument(file, exercise_id, session):
        exercise = query_exercise_by_id(exercise_id, session)
        log.info("Validating if instrument is already uploaded for this exercise", exercise_id=exercise_id)
        if exercise:
            for i in exercise.instruments:
                if i.type == "SEFT" and i.seft_file.file_name == file.filename:
                    log.info(
                        "Collection instrument file already uploaded for this collection exercise",
                        exercise_id=exercise_id,
                    )
                    raise RasError("Collection instrument file already uploaded for this collection exercise", 400)
        log.info("Successfully validated instrument is not already uploaded for this exercise", exercise_id=exercise_id)
        return

    @with_db_session
    def patch_seft_instrument(self, instrument_id: str, file, session):
        """
        Replaces the seft_file for an instrument with the one provided.

        :param instrument_id: The top level instrument id that needs changing
        :param file: A FileStorage object with the new file
        :param session: A database session
        :raises RasError: Raised when instrument id is invalid, instrument not found, or instrument isn't of type SEFT
        """
        validate_uuid(instrument_id)
        instrument = self.get_instrument_by_id(instrument_id, session)
        if instrument is None:
            log.error("Instrument not found")
            raise RasError("Instrument not found", 400)
        if instrument.type != "SEFT":
            log.error("Not a SEFT instrument")
            raise RasError("Not a SEFT instrument", 400)

        survey_ref = get_survey_details(instrument.survey.survey_id).get("surveyRef")
        exercise_id = str(instrument.exids[0])

        seft_model = self._update_seft_file(instrument.seft_file, file, survey_ref, exercise_id)
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
                bound_logger.info("Reporting unit has had collection instruments uploaded for it in the past")

                for related_exercise in instrument.exercises:
                    related_exercise_id = related_exercise.exercise_id
                    exercise_id = exercise.exercise_id
                    bound_logger.bind(exercise_id=exercise_id, related_exercise_id=related_exercise_id)
                    bound_logger.info("About to check exercise for match")
                    if related_exercise_id == exercise_id:
                        bound_logger.info(
                            "Was about to add a second instrument for a reporting unit for a " "collection exercise"
                        )
                        ru_ref = business.ru_ref
                        error_text = (
                            f"Reporting unit {ru_ref} already has an instrument "
                            f"uploaded for this collection exercise"
                        )
                        raise RasError(error_text, 400)
        bound_logger.info("Successfully validated there isn't an instrument for this ru for this exercise")

    @with_db_session
    def upload_eq(self, survey_id, classifiers=None, session=None):
        """
        Upload an eQ collection instrument to the db

        :param classifiers: Classifiers associated with the instrument
        :param session: database session
        :param survey_id: database session
        :return: a collection instrument instance
        """

        log.info("Upload instrument", survey_id=survey_id)

        validate_uuid(survey_id)
        survey = self._find_or_create_survey_from_survey_id(survey_id, session)
        survey_service_details = get_survey_details(survey.survey_id)
        ci_type = "EQ"
        instrument = InstrumentModel(ci_type=ci_type)
        instrument.survey = survey
        if classifiers:
            classifiers = loads(classifiers)
            if survey_service_details["surveyMode"] == "EQ_AND_SEFT":
                self.validate_eq_and_seft_form_type(survey.survey_id, classifiers.get("form_type"), ci_type, session)

            deserialized_classifiers = classifiers
            instruments = self._get_instruments_by_classifier(deserialized_classifiers, None, session)
            for instrument in instruments:
                if instrument.classifiers == deserialized_classifiers:
                    raise RasError("Cannot upload an instrument with an identical set of classifiers", 400)

            instrument.classifiers = deserialized_classifiers
        session.add(instrument)
        return instrument

    @with_db_session
    def update_exercise_eq_instruments(self, exercise_id: str, instruments: list, session=None) -> bool:
        """
        Updates eQ instruments used by an exercise. Current instruments are used to determine which ones should be
        appended and/or removed.
        :param exercise_id: The collection exercise id
        :param instruments: A list of instruments that the collection exercise should now have
        :param session: database session
        :return: a bool
        """

        validate_uuid(exercise_id)
        exercise = self._find_or_create_exercise(exercise_id, session)
        current_instruments = [str(instrument.instrument_id) for instrument in exercise.instruments]

        instruments_to_add = set(instruments).difference(current_instruments)
        instruments_to_remove = set(current_instruments).difference(instruments)

        for instrument_id in instruments_to_add:
            instrument = self.get_instrument_by_id(instrument_id, session)
            instrument.exercises.append(exercise)

        for instrument_id in instruments_to_remove:
            instrument = self.get_instrument_by_id(instrument_id, session)
            instrument.exercises.remove(exercise)

        log.info("Collection instruments updated successfully", instruments=instruments, exercise_id=exercise_id)

        return bool(instruments_to_add or instruments_to_remove)

    @with_db_session
    def link_instrument_to_exercise(self, instrument_id, exercise_id, session=None):
        """
        Link a collection instrument to a collection exercise

        :param instrument_id: A collection instrument id (UUID)
        :param exercise_id: A collection exercise id (UUID)
        :param session: database session
        :return: True if instrument has been successfully linked to exercise
        """
        log.info("Linking instrument to exercise", instrument_id=instrument_id, exercise_id=exercise_id)
        validate_uuid(instrument_id)
        validate_uuid(exercise_id)

        instrument = self.get_instrument_by_id(instrument_id, session)
        exercise = self._find_or_create_exercise(exercise_id, session)
        instrument.exercises.append(exercise)

        log.info("Successfully linked instrument to exercise", instrument_id=instrument_id, exercise_id=exercise_id)
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
        bound_logger.info("Unlinking instrument and exercise")

        instrument = self.get_instrument_by_id(instrument_id, session)
        exercise = self.get_exercise_by_id(exercise_id, session)
        if not instrument or not exercise:
            bound_logger.info("Failed to unlink, unable to find instrument or exercise")
            raise RasError("Unable to find instrument or exercise", 404)

        if instrument.type == "SEFT":
            # SEFT instruments need to be deleted from both GCP and the db, removing just the link will leave orphaned
            # data. When deleting SEFT instruments, the link will automatically be removed without this function
            raise RasError(
                f"{instrument_id} is of type SEFT which should be deleted and not unlinked",
                405,
            )

        instrument.exercises.remove(exercise)
        bound_logger.info("Successfully unlinked instrument to exercise")
        return True

    @with_db_session
    def delete_collection_instrument(self, instrument_id: str, session: Session = None) -> None:
        """
        Deletes a collection instrument from the database and gcs (if the instrument is a SEFT)
        :param instrument_id: A collection instrument id (UUID)
        :param session: database session
        """
        instrument = self.get_instrument_by_id(instrument_id, session)

        if not instrument:
            raise RasError(f"Collection instrument {instrument_id} not found", 404)

        session.delete(instrument)

        if instrument.type == "SEFT":
            gcs_seft_bucket = GoogleCloudSEFTCIBucket(current_app.config)
            file_path = self._build_seft_file_path(instrument)
            gcs_seft_bucket.delete_file_from_bucket(file_path)

    @with_db_session
    def delete_collection_instruments_by_exercise(self, ce_id: str, session: Session = None):
        """
        Deletes all collection instruments associated with a collection exercise from the database and GCP
        :param ce_id: A collection exercise id (UUID)
        :param session: database session
        """
        exercise = self.get_exercise_by_id(ce_id, session)
        if not exercise:
            return COLLECTION_EXERCISE_NOT_FOUND_IN_DB, 404

        session.delete(exercise)

        if exercise.seft_instrument_in_exercise:
            survey_id = exercise.instruments[0].survey.survey_id
            survey_ref = get_survey_details(survey_id).get("surveyRef")
            prefix = f"{survey_ref}/{ce_id}"
            gcs_seft_bucket = GoogleCloudSEFTCIBucket(current_app.config)
            try:
                gcs_seft_bucket.delete_files_by_prefix(prefix)
            except GCPBucketException:
                return COLLECTION_EXERCISE_NOT_FOUND_ON_GCP, 404

        return COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED, 200

    @staticmethod
    def _find_or_create_survey_from_exercise_id(exercise_id, session):
        """
        Makes a request to the collection exercise service for the survey ID,
        reuses the survey if it exists in this service or create if it doesn't
        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return: A survey record
        """
        response = service_request(
            service="collectionexercise-service", endpoint="collectionexercises", search_value=exercise_id
        )
        survey_id = response.json().get("surveyId")

        survey = query_survey_by_id(survey_id, session)
        if not survey:
            log.info("creating survey", survey_id=survey_id)
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
            log.info("creating survey", survey_id=survey_id)
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
            log.info("creating exercise", exercise_id=exercise_id)
            exercise = ExerciseModel(exercise_id=exercise_id)
        return exercise

    @staticmethod
    def get_exercise_by_id(exercise_id, session):
        """
        Retrieves exercise

        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return: exercise
        """
        log.info("Searching for exercise", exercise_id=exercise_id)
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
            log.info("creating business", ru_ref=ru_ref)
            business = BusinessModel(ru_ref=ru_ref)
        return business

    @staticmethod
    def _create_seft_file(instrument_id, file):
        """
        Creates a seft_file with an encrypted version of the file
        :param file: A file object from which we can read the file contents
        :return: instrument
        """
        log.info("creating instrument seft file")
        file_contents = file.read()
        file_size = len(file_contents)
        seft_file = SEFTModel(instrument_id=instrument_id, file_name=file.filename, length=file_size)

        return seft_file

    @staticmethod
    def _update_seft_file(seft_model, file, survey_ref, exercise_id):
        """
        Updates a seft_file with a new version of the data

        :param file: A file object from which we can read the file contents
        :return: instrument
        """
        log.info("Updating instrument seft file")
        file_contents = file.read()
        file_size = len(file_contents)
        if file_size == 0:
            raise RasError("File is empty", 400)
        seft_model.length = file_size
        old_filename = seft_model.file_name
        seft_model.file_name = file.filename
        file.filename = survey_ref + "/" + exercise_id + "/" + file.filename
        old_filename = survey_ref + "/" + exercise_id + "/" + old_filename
        seft_ci_bucket = GoogleCloudSEFTCIBucket(current_app.config)
        seft_ci_bucket.delete_file_from_bucket(old_filename)
        seft_ci_bucket.upload_file_to_bucket(file=file)
        return seft_model

    @with_db_session
    def get_instruments_by_exercise_id_csv(self, exercise_id, session=None):
        """
        Finds all collection instruments associated with an exercise and returns them in csv format

        :param exercise_id
        :param session: database session
        :return: collection instruments in csv
        """
        log.info("Getting csv for instruments", exercise_id=exercise_id)

        validate_uuid(exercise_id)
        csv_format = '"{count}","{file_name}","{length}","{date_stamp}"\n'
        count = 1
        csv = csv_format.format(count="Count", file_name="File Name", length="Length", date_stamp="Time Stamp")
        exercise = query_exercise_by_id(exercise_id, session)

        if not exercise:
            return None

        for instrument in exercise.instruments:
            try:
                file_path = self._build_seft_file_path(instrument)
                seft_ci_bucket = GoogleCloudSEFTCIBucket(current_app.config)
                file = seft_ci_bucket.download_file_from_bucket(file_path)
                csv += csv_format.format(
                    count=count,
                    file_name=instrument.seft_file.file_name,
                    length=len(file),
                    date_stamp=instrument.stamp,
                )
            except Exception:
                log.exception("Couldn't find SEFT CI in bucket")
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

    @with_db_session
    def get_instrument_data(self, instrument_id, session):
        """
        Get the instrument data from the db or bucket using the id

        :param instrument_id: The id of the instrument we want
        :param session: database session
        :return: data and file_name
        """

        instrument = CollectionInstrument.get_instrument_by_id(instrument_id, session)

        data = None
        file_name = None

        if instrument:
            try:
                file_path = self._build_seft_file_path(instrument)
                seft_ci_bucket = GoogleCloudSEFTCIBucket(current_app.config)
                file = seft_ci_bucket.download_file_from_bucket(file_path)
                return file, instrument.seft_file.file_name
            except Exception:
                log.exception("Couldn't find SEFT CI in GCP bucket")
        return data, file_name

    @staticmethod
    def get_instrument_by_id(instrument_id, session):
        """
        Get the collection instrument from the db using the id

        :param instrument_id: The id of the instrument we want
        :param session: database session
        :return: instrument
        """
        log.info("Searching for instrument", instrument_id=instrument_id)
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
            if classifier == "RU_REF":
                query = query.filter(BusinessModel.ru_ref == value)
            elif classifier == "COLLECTION_EXERCISE":
                query = query.filter(ExerciseModel.exercise_id == value)
            elif classifier == "SURVEY_ID":
                query = query.filter(SurveyModel.survey_id == value)
            elif classifier == "TYPE":
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
        log.info("creating model joins for search")

        query = query_instrument(session)
        already_joined = []
        for classifier in json_search_parameters.keys():
            if classifier == "RU_REF" and BusinessModel not in already_joined:
                query = query.join(BusinessModel, InstrumentModel.businesses)
                already_joined.append(BusinessModel)
            elif classifier == "COLLECTION_EXERCISE" and ExerciseModel not in already_joined:
                query = query.join(ExerciseModel, InstrumentModel.exercises)
                already_joined.append(ExerciseModel)
            elif classifier == "SURVEY_ID" and SurveyModel not in already_joined:
                query = query.join(SurveyModel, InstrumentModel.survey)
                already_joined.append(SurveyModel)
        return query

    @staticmethod
    def _build_seft_file_path(instrument) -> str:
        survey_ref = get_survey_details(instrument.survey.survey_id).get("surveyRef")
        exercise_id = str(instrument.exids[0])
        return f"{survey_ref}/{exercise_id}/{instrument.seft_file.file_name}"
