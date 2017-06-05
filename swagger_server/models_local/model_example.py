import datetime
import enum

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Enum

from swagger_server.models_local.base import Base
from swagger_server.models_local.guid import GUID

"""
All model classes should inherit from the Base which is imported above. The database initialisation step will
then automatically set the schema for the model entities when necessary (i.e. when using postgres).
"""


class ChildStatusEnumExample(enum.Enum):
    THIS_STATE = 0
    THAT_STATE = 1


class Parent(Base):

    __tablename__ = 'parent'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    children = relationship("Child", back_populates="parent")
    created_on = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, name):
        self.name = name


class Child(Base):
    __tablename__ = 'child'

    id = Column(Integer, primary_key=True)
    name = Column(Text)
    parent_id = Column(Integer, ForeignKey('parent.id'))
    parent = relationship("Parent", back_populates="children")
    status = Column('status', Enum(ChildStatusEnumExample))
    created_on = Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, name, status):
        self.name = name
        self.status = status
