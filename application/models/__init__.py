import copy
import json
import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext import mutable
from sqlalchemy.types import CHAR, TypeDecorator, Unicode

json_null = object()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses
    CHAR(32), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    @staticmethod
    def load_dialect_impl(dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(UUID())
        else:
            return dialect.type_descriptor(CHAR(32))

    @staticmethod
    def process_bind_param(value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return str(value)
        else:
            if not isinstance(value, uuid.UUID):
                return "%.32x" % uuid.UUID(value).int
            else:
                # hexstring
                return "%.32x" % value.int

    @staticmethod
    def process_result_value(value, dialect):
        if value is None:
            return value
        else:
            return uuid.UUID(value)


# FIXME: this stores JSON in postgres as CHARACTER VARYING rather than native json/jsonb
class JsonColumn(TypeDecorator):
    impl = Unicode

    @staticmethod
    def load_dialect_impl(dialect):
        if dialect.name == "postgresql":
            from sqlalchemy.dialects import postgresql

            return dialect.type_descriptor(postgresql.JSONB())
        else:
            return dialect.type_descriptor(String())

    @staticmethod
    def process_bind_param(value, dialect):
        if value is json_null:
            value = None
        return json.dumps(value)

    @staticmethod
    def process_result_value(value, dialect):
        if value is None:
            return None
        return json.loads(value)

    @staticmethod
    def copy_value(value):
        return copy.deepcopy(value)


mutable.MutableDict.associate_with(JsonColumn)
