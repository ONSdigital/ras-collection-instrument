from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer
from .guid import GUID
from ons_ras_common import ons_env


class SurveyModel(ons_env.db.base):
    """
    This models the 'business' table which is a placeholder for thr RU code
    """
    __tablename__ = 'survey'
    __table_args__ = None if not ons_env.get('db_schema') else {'schema': ons_env.get('db_schema')}

    id = Column(Integer, primary_key=True)
    survey_id = Column(GUID, index=True)
    # instruments = relationship('InstrumentModel', back_populates='survey')

    def __init__(self, survey_id=None, items=0, status='pending'):
        """Initialise the class with optionally supplied defaults"""
        self.survey_id = survey_id
        self.items = items
        self.status = status
