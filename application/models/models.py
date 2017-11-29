from .associations import instrument_exercise_table, instrument_business_table
from datetime import datetime
from ras_common_utils.ras_database.base import Base
from ras_common_utils.ras_database.guid import GUID
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP, LargeBinary, Enum, String
from uuid import uuid4


class InstrumentModel(Base):
    """
    This models the 'instrument' table which keeps the stored collection instruments
    """
    __tablename__ = 'instrument'

    id = Column(Integer, primary_key=True, autoincrement=True)
    instrument_id = Column(GUID, index=True)
    data = Column(LargeBinary)
    len = Column(Integer)
    stamp = Column(TIMESTAMP)
    survey_id = Column(Integer, ForeignKey('survey.id'))
    survey = relationship('SurveyModel', back_populates='instruments')

    classifications = relationship('ClassificationModel', back_populates='instrument')
    exercises = relationship('ExerciseModel', secondary=instrument_exercise_table, back_populates='instruments')
    businesses = relationship('BusinessModel', secondary=instrument_business_table, back_populates='instruments')

    def __init__(self, data=None, length=0):
        """Initialise the class with optionally supplied defaults"""
        self.data = data
        self.len = length
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


class BusinessModel(Base):
    """
    This models the 'business' table which is a placeholder for the RU code
    """
    __tablename__ = 'business'

    id = Column(Integer, primary_key=True)
    ru_ref = Column(String(32), index=True)
    instruments = relationship('InstrumentModel', secondary=instrument_business_table, back_populates='businesses')

    def __init__(self, ru_ref=None, items=0, status='pending'):
        """Initialise the class with optionally supplied defaults"""
        self.ru_ref = ru_ref
        self.items = items
        self.status = status


class ClassificationModel(Base):
    """
    This models the 'classifier' table which keeps tracks tags against an instrument
    """
    __tablename__ = 'classification'
    classifications = ('LEGAL_STATUS', 'INDUSTRY', 'SIZE', 'GEOGRAPHY')
    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey('instrument.id'))
    instrument = relationship('InstrumentModel', back_populates='classifications')
    kind = Column(Enum('LEGAL_STATUS', 'INDUSTRY', 'SIZE', 'GEOGRAPHY', 'COLLECTION_EXERCISE', 'RU_REF', name='kind'))
    value = Column(String(64))

    def __init__(self, kind=None, value=None):
        """Initialise the class with optionally supplied defaults"""
        self.kind = kind
        self.value = value


class ExerciseModel(Base):
    """
    This models the 'exercise' table which keeps the stored collection instruments
    """
    __tablename__ = 'exercise'

    id = Column(Integer, primary_key=True)
    exercise_id = Column(GUID, index=True)
    items = Column(Integer)
    status = Column(Enum('uploading', 'pending', 'active', name='status'))
    instruments = relationship('InstrumentModel', secondary=instrument_exercise_table, back_populates='exercises')

    def __init__(self, exercise_id=None, items=0, status='pending'):
        """Initialise the class with optionally supplied defaults"""
        self.exercise_id = exercise_id
        self.items = items
        self.status = status


class SurveyModel(Base):
    """
    This models the 'business' table which is a placeholder for the RU code
    """
    __tablename__ = 'survey'

    id = Column(Integer, primary_key=True)
    survey_id = Column(GUID, index=True)
    instruments = relationship('InstrumentModel', back_populates='survey')

    def __init__(self, survey_id=None, items=0, status='pending'):
        """Initialise the class with optionally supplied defaults"""
        self.survey_id = survey_id
        self.items = items
        self.status = status
