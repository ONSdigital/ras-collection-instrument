from app import db
from sqlalchemy.dialects.postgresql import *
import datetime
from sqlalchemy import *


class Result(db.Model):
    __tablename__ = 'ras_collection_instruments'
    id = db.Column(db.Integer, primary_key=True)
    file_uuid = db.Column(UUID)
    content = db.Column(JSON)
    created_on = db.Column(DateTime, default=datetime.datetime.utcnow)

    def __init__(self, file_uuid, content):
        self.file_uuid = file_uuid
        self.content = content
        # self.created_on = created_on
