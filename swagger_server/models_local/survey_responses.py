from sqlalchemy import Column
from sqlalchemy.types import TIMESTAMP, Integer, LargeBinary, String
from datetime import datetime
from ..configuration import ons_env
from .guid import GUID
from uuid import uuid4
from .base import Base


class SurveyResponseModel(Base):
    """
        This models the 'survey response' table
    """
    __tablename__ = 'survey_responses'
    __table_args__ = ons_env.get('db_schema')

    id = Column(Integer, primary_key=True, autoincrement=True)
    file_name = Column(String)
    case_id = Column(Integer)
    encrypted_file = Column(LargeBinary)
    file_size = Column(Integer)
    date_time_stamp = Column(TIMESTAMP)
    survey_response_id = Column(GUID, index=True)

    def __init__(self, file_name, encrypted_file, case_id, file_size):
        self.file_name = file_name
        self.encrypted_file = encrypted_file
        self.case_id = case_id
        self.file_size = file_size
        self.stamp = datetime.now()
        self.survey_response_id = uuid4()
        self.date_time_stamp = datetime.now()

    @property
    def json(self):
        """Return a JSON representation of this record"""
        return {
            'id': self.id,
            'case_id': self.case_id,
            'file_size': self.file_size,
            'date_time_stamp': self.date_time_stamp,
            'survey_response_id': self.survey_response_id,
            'file_name': self.file_name
        }
