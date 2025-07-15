from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
    RegistryInstrumentModel,
    SurveyModel,
)


def query_exercise_by_id(exercise_id, session):
    return session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).first()


def query_business_by_ru(ru_ref, session):
    return session.query(BusinessModel).filter(BusinessModel.ru_ref == ru_ref).first()


def query_survey_by_id(survey_id, session):
    return session.query(SurveyModel).filter(SurveyModel.survey_id == survey_id).first()


def query_instrument_by_id(instrument_id, session):
    return session.query(InstrumentModel).filter(InstrumentModel.instrument_id == instrument_id).first()


def query_instrument(session):
    return session.query(InstrumentModel)


def query_instruments_form_type_with_different_survey_mode(survey_id, form_type, survey_mode, session):
    """
    query to find instruments which match a given survey_id and form_type but not the survey mode
    :param survey_id: survey id
    :param form_type: form type (i.e 0001)
    :param survey_mode: survey mode (i.e eQ)
    :param session: session
    :return: InstrumentModel
    """
    return (
        session.query(InstrumentModel)
        .join(SurveyModel)
        .filter(
            SurveyModel.survey_id == survey_id,
            InstrumentModel.classifiers["form_type"].astext == form_type,
            InstrumentModel.type != survey_mode,
        )
        .all()
    )


def query_registry_instruments_by_exercise_id(exercise_id, session):
    return session.query(RegistryInstrumentModel).filter(RegistryInstrumentModel.exercise_id == exercise_id)


def query_registry_instrument_by_exercise_id_and_formtype(exercise_id, form_type, session):
    return session.query(RegistryInstrumentModel).filter(
        RegistryInstrumentModel.exercise_id == exercise_id,
        RegistryInstrumentModel.classifier_type == "form_type",
        RegistryInstrumentModel.classifier_value == form_type,
    )


def query_registry_instrument_count_by_exercise_id(exercise_id: str, session: Session) -> Optional[int]:
    return session.execute(
        text("SELECT * FROM ras_ci.registry_instrument_count WHERE exercise_id = :exercise_id"),
        {"exercise_id": exercise_id}
    ).first()
