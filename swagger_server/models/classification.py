from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, Enum, String
from ons_ras_common import ons_env

prefix = ons_env.get('db_schema')+'.' if ons_env.get('db_schema') else ''
classifications = ('LEGAL_STATUS', 'INDUSTRY', 'SIZE', 'GEOGRAPHY', 'COLLECTION_EXERCISE', 'RU_REF')


class ClassificationModel(ons_env.db.base):
    """
    This models the 'classifier' table which keeps tracks tags against an instrument
    """
    __tablename__ = 'classification'
    __table_args__ = None if not ons_env.get('db_schema') else {'schema': ons_env.get('db_schema')}

    id = Column(Integer, primary_key=True)
    instrument_id = Column(Integer, ForeignKey(prefix+'instrument.id'))
    instrument = relationship('InstrumentModel', back_populates='classifications')
    kind = Column(Enum('LEGAL_STATUS', 'INDUSTRY', 'SIZE', 'GEOGRAPHY', 'COLLECTION_EXERCISE', 'RU_REF', name='kind'))
    value = Column(String(64))

    def __init__(self, kind=None, value=None):
        """Initialise the class with optionally supplied defaults"""
        self.kind = kind
        self.value = value