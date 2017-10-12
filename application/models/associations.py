from sqlalchemy import Table, Column, Integer, ForeignKey
from ras_common_utils.ras_database.base import Base

instrument_exercise_table = Table('instrument_exercise', Base.metadata,
                                  Column('instrument_id', Integer, ForeignKey('instrument.id')),
                                  Column('exercise_id', Integer, ForeignKey('exercise.id')))

instrument_business_table = Table('instrument_business', Base.metadata,
                                  Column('instrument_id', Integer, ForeignKey('instrument.id')),
                                  Column('business_id', Integer, ForeignKey('business.id')))
