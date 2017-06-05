from sqlalchemy import Table, Column, Integer, ForeignKey
from ..configuration import ons_env
from .base import Base

prefix = ons_env.get('db_schema')+'.' if ons_env.get('db_schema') else ''
schema = ons_env.get('db_schema') if ons_env.get('db_schema') else None

instrument_exercise_table = Table('instrument_exercise', Base.metadata,
    Column('instrument_id', Integer, ForeignKey(prefix+'instrument.id')),
    Column('exercise_id', Integer, ForeignKey(prefix+'exercise.id')),
    schema=schema
)

instrument_business_table = Table('instrument_business', Base.metadata,
    Column('instrument_id', Integer, ForeignKey(prefix+'instrument.id')),
    Column('business_id', Integer, ForeignKey(prefix+'business.id')),
    schema=schema
)
