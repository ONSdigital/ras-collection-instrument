"""
This module contains the data model for the collection instrument
"""

import datetime

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import TEXT, JSON, UUID

from app import db


class CollectionInstrument(db.Model):
    """
    The collection instrument model
    """
    __tablename__ = 'ras_collection_instruments'
    id = db.Column(db.Integer, primary_key=True)
    urn = db.Column(TEXT)
    survey_urn = db.Column(TEXT)
    content = db.Column(JSON)
    file_uuid = db.Column(UUID)
    file_path = db.Column(TEXT)
    created_on = db.Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, urn, survey_urn, content, id=None, file_uuid=None, file_path=None):
        self.id = id
        self.urn = urn
        self.survey_urn = survey_urn
        self.content = content
        self.file_uuid = file_uuid
        self.file_path = file_path
