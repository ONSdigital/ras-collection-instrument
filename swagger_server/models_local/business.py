from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, String
from .associations import instrument_business_table
from ons_ras_common import ons_env


class BusinessModel(ons_env.db.base):
    """
    This models the 'business' table which is a placeholder for thr RU code
    """
    __tablename__ = 'business'
    __table_args__ = None if not ons_env.get('db_schema') else {'schema': ons_env.get('db_schema')}

    id = Column(Integer, primary_key=True)
    ru_ref = Column(String(32), index=True)
    instruments = relationship('InstrumentModel', secondary=instrument_business_table, back_populates='businesses')

    def __init__(self, ru_ref=None, items=0, status='pending'):
        """Initialise the class with optionally supplied defaults"""
        self.ru_ref = ru_ref
        self.items = items
        self.status = status
