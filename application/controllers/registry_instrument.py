import logging

import structlog

from application.controllers.helper import validate_uuid
from application.controllers.session_decorator import with_db_session
from application.controllers.sql_queries import (
    query_registry_instrument_by_exercise_id_and_formtype,
    query_registry_instruments_by_exercise_id,
)

log = structlog.wrap_logger(logging.getLogger(__name__))


class RegistryInstrument(object):
    @with_db_session
    def get_registry_instruments_by_exercise_id(self, exercise_id, session=None):
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
    def get_registry_instrument_by_exercise_id_and_formtype(self, exercise_id, form_type, session=None):
        """
        Retrieves a selected CIR instrument for the given collection exercise and form type

        :param exercise_id: An exercise id (UUID)
        :param form_type: The form type (e.g. "0001")
        :param session: database session
        :return: A RegistryInstrumentModel object
        """
        log.info("Retrieving a selected CIR instrument", exercise_id=exercise_id, form_type=form_type)
        validate_uuid(exercise_id)
        registry_instrument = query_registry_instrument_by_exercise_id_and_formtype(
            exercise_id, form_type, session
        ).first()

        if registry_instrument is not None:
            return registry_instrument.to_dict()
        return None
