import logging

import structlog

from application.controllers.helper import validate_uuid
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import (
    query_registry_instrument_by_exercise_id_and_formtype,
    query_registry_instruments_by_exercise_id,
)
from application.models.models import RegistryInstrumentModel

log = structlog.wrap_logger(logging.getLogger(__name__))


class RegistryInstrument(object):
    @with_db_session
    def get_by_exercise_id(self, exercise_id, session=None):
        """
        Retrieves a list of selected CIR instruments for the given collection exercise

        :param exercise_id: An exercise id (UUID)
        :param session: database session
        :return: a list of RegistryInstrumentModel dictionaries
        """
        log.info("Retrieving list of selected CIR instruments", exercise_id=exercise_id)
        validate_uuid(exercise_id)
        registry_instruments = query_registry_instruments_by_exercise_id(exercise_id, session)

        response = []
        for registry_instrument in registry_instruments:
            response.append(registry_instrument.to_dict())
        return response

    @with_db_session
    def get_by_exercise_id_and_formtype(self, exercise_id, form_type, session=None):
        """
        Retrieves the selected CIR instrument for the given collection exercise and form type

        :param exercise_id: An exercise id (UUID)
        :param form_type: The form type (e.g. "0001")
        :param session: database session
        :return: A RegistryInstrumentModel object, or None if not found
        """
        log.info("Retrieving a selected CIR instrument", exercise_id=exercise_id, form_type=form_type)
        validate_uuid(exercise_id)
        registry_instrument = query_registry_instrument_by_exercise_id_and_formtype(
            exercise_id, form_type, session
        ).first()

        if registry_instrument is not None:
            return registry_instrument.to_dict()
        return None

    @with_db_session
    def save_for_exercise_id_and_formtype(
        self, survey_id, exercise_id, instrument_id, form_type, ci_version, published_at, guid, session=None
    ):
        """
        Save a selected CIR instrument for the given collection exercise and form type

        :param exercise_id: An exercise id (UUID)
        :param form_type: The form type (e.g. "0001")
        :param session: database session
        :return: True if successful, and is_new indicating if a new object was created
        """

        registry_instrument, is_new = self._find_or_create(
            survey_id, exercise_id, instrument_id, form_type, ci_version, published_at, guid, session
        )

        session.add(registry_instrument)
        return True, is_new

    @with_db_session
    def delete_by_exercise_id_and_formtype(self, exercise_id, form_type, session=None):
        """
        Delete the selected CIR instrument for the given collection exercise and form type

        :param exercise_id: An exercise id (UUID)
        :param form_type: The form type (e.g. "0001")
        :param session: database session
        :return: A boolean indicating success
        """
        log.info("Deleting a selected CIR instrument", exercise_id=exercise_id, form_type=form_type)
        validate_uuid(exercise_id)
        registry_instrument = query_registry_instrument_by_exercise_id_and_formtype(
            exercise_id, form_type, session
        ).first()

        if registry_instrument is None:
            return False

        session.delete(registry_instrument)
        return True

    @staticmethod
    def _find_or_create(survey_id, exercise_id, instrument_id, form_type, ci_version, published_at, guid, session):
        """
        Retrieves an existing selected RegistryInstrumentModel object from the db if it exists,
        or creates a new RegistryInstrumentModel object if it doesn't exist

        :param exercise_id: An exercise id (UUID)
        :param form_type: The form type (e.g. "0001")
        :param session: database session
        :return: RegistryInstrumentModel object
        """

        validate_uuid(exercise_id)
        registry_instrument = query_registry_instrument_by_exercise_id_and_formtype(
            exercise_id, form_type, session
        ).first()

        if not registry_instrument:
            log.info("Registry instrument NOT found, creating", exercise_id=exercise_id, form_type=form_type)
            registry_instrument = RegistryInstrumentModel()
            registry_instrument.survey_id = survey_id
            registry_instrument.exercise_id = exercise_id
            registry_instrument.instrument_id = instrument_id
            registry_instrument.classifier_type = "form_type"
            registry_instrument.classifier_value = form_type
            registry_instrument.ci_version = ci_version
            registry_instrument.guid = guid
            registry_instrument.published_at = published_at
            is_new = True
        else:
            log.info("Registry instrument found, updating", exercise_id=exercise_id, form_type=form_type)
            registry_instrument.ci_version = ci_version
            registry_instrument.guid = guid
            registry_instrument.published_at = published_at
            is_new = False

        return registry_instrument, is_new
