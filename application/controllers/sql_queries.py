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
