from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
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


def query_instrument_by_exercise_id(exercise_id, session):
    session.query.join(ExerciseModel, InstrumentModel.exercises)
    return session.query(InstrumentModel).filter(InstrumentModel.exids == exercise_id)
