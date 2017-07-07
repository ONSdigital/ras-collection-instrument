from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP, Integer, LargeBinary
from datetime import datetime
from .associations import instrument_exercise_table, instrument_business_table
from .guid import GUID
from uuid import uuid4
from ons_ras_common import ons_env

prefix = ons_env.get('db_schema')+'.' if ons_env.get('db_schema') else ''


class InstrumentModel(ons_env.db.base):
    """
    This models the 'instrument' table which keeps the stored collection instruments
    """
    __tablename__ = 'instrument'
    __table_args__ = None if not ons_env.get('db_schema') else {'schema': ons_env.get('db_schema')}

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(GUID, index=True)
    data = Column(LargeBinary)
    len = Column(Integer)
    stamp = Column(TIMESTAMP)
    survey_id = Column(Integer, ForeignKey(prefix+'survey.id'))
    survey = relationship('SurveyModel', back_populates='instruments')

    classifications = relationship('ClassificationModel', back_populates='instrument')
    exercises = relationship('ExerciseModel', secondary=instrument_exercise_table, back_populates='instruments')
    businesses = relationship('BusinessModel', secondary=instrument_business_table, back_populates='instruments')

    def __init__(self, data=None, len=0):
        """Initialise the class with optionally supplied defaults"""
        self.data = data
        self.len = len
        self.stamp = datetime.now()
        self.instrument_id = uuid4()

    @property
    def json(self):
        return {
            'id': self.instrument_id,
            'len': self.len,
            'stamp': self.stamp,
            'survey': self.survey.survey_id,
            'businesses': self.rurefs,
            'exercises': self.exids,
            'classifiers': self.classifiers
        }


    @property
    def rurefs(self):
        return [business.ru_ref for business in self.businesses]

    @property
    def exids(self):
        return [exercise.exercise_id for exercise in self.exercises]

    @property
    def classifiers(self):
        return [{classifier.kind: classifier.value} for classifier in self.classifications]
