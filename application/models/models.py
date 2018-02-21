from datetime import datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import TIMESTAMP, LargeBinary, Enum, String
from sqlalchemy.dialects.postgresql.json import JSONB
from uuid import uuid4

from application.models import GUID


Base = declarative_base()


instrument_exercise_table = Table('instrument_exercise', Base.metadata,
                                  Column('instrument_id', Integer, ForeignKey('instrument.id')),
                                  Column('exercise_id', Integer, ForeignKey('exercise.id')))

instrument_business_table = Table('instrument_business', Base.metadata,
                                  Column('instrument_id', Integer, ForeignKey('instrument.id')),
                                  Column('business_id', Integer, ForeignKey('business.id')))


class InstrumentModel(Base):
    """
    This models the 'instrument' table which keeps the stored collection instruments
    """
    __tablename__ = 'instrument'

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(8))
    instrument_id = Column(GUID, unique=True, index=True)
    stamp = Column(TIMESTAMP)
    survey_id = Column(Integer, ForeignKey('survey.id'))
    classifiers = Column(JSONB)
    survey = relationship('SurveyModel', back_populates='instruments')
    seft_file = relationship("SEFTModel", uselist=False, back_populates="instrument")

    exercises = relationship('ExerciseModel', secondary=instrument_exercise_table, back_populates='instruments')
    businesses = relationship('BusinessModel', secondary=instrument_business_table, back_populates='instruments')

    def __init__(self, classifiers=None, ci_type=None):
        """Initialise the class with optionally supplied defaults"""
        self.stamp = datetime.now()
        self.instrument_id = uuid4()
        self.classifiers = classifiers
        self.type = ci_type

    @property
    def json(self):
        return {
            'id': self.instrument_id,
            'file_name': self.seft_file.file_name,
            'len': self.seft_file.len,
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


class BusinessModel(Base):
    """
    This models the 'business' table which is a placeholder for the RU code
    """
    __tablename__ = 'business'

    id = Column(Integer, primary_key=True)
    ru_ref = Column(String(32), index=True)
    instruments = relationship('InstrumentModel', secondary=instrument_business_table, back_populates='businesses')

    def __init__(self, ru_ref=None):
        """Initialise the class with optionally supplied defaults"""
        self.ru_ref = ru_ref


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

    def __init__(self, survey_id=None):
        """Initialise the class with optionally supplied defaults"""
        self.survey_id = survey_id


class SEFTModel(Base):
    """
    This models the 'seft_instrument' table which keeps the stored seft collection instruments
    """
    __tablename__ = 'seft_instrument'

    id = Column(Integer, primary_key=True)
    file_name = Column(String(32))
    data = Column(LargeBinary)
    len = Column(Integer)
    instrument_id = Column(GUID, ForeignKey('instrument.instrument_id'))

    instrument = relationship("InstrumentModel", back_populates="seft_file")

    def __init__(self, instrument_id=None, file_name=None, length=None, data=None):
        """Initialise the class with optionally supplied defaults"""
        self.instrument_id = instrument_id
        self.file_name = file_name
        self.len = length
        self.data = data
