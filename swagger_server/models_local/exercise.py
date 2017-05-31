from sqlalchemy import Column
from sqlalchemy.orm import relationship
from sqlalchemy.types import Integer, Enum
from ..configuration import ons_env
from .associations import instrument_exercise_table
from .guid import GUID

class ExerciseModel(ons_env.base):
    """
    This models the 'exercise' table which keeps the stored collection instruments
    """
    __tablename__ = 'exercise'
    __table_args__ = None if not ons_env.get('db_schema') else {'schema': ons_env.get('db_schema')}

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

    @property
    def json(self):
        """Return a JSON representation of this record"""
        return {
            'id': self.exercise_id,
            'count': self.items,
            'status': self.status,
            'current': len(self.instruments)
        }

