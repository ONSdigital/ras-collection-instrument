from app import db
from sqlalchemy.dialects.postgresql import *
import datetime
from sqlalchemy import *


class Result(db.Model):
    __tablename__ = 'ras_collection_instruments'
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(UUID)
    content = db.Column(JSON)
    file_path = db.Column(TEXT)
    created_on = db.Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, file_uuid, content, file_path=None):
        self.file_uuid = file_uuid
        self.content = content
        self.file_path = file_path
        # self.created_on = created_on
