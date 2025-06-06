from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, ForeignKey, Integer, Table
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.types import TIMESTAMP, UUID, String

Base = declarative_base()

instrument_exercise_table = Table(
    "instrument_exercise",
    Base.metadata,
    Column("instrument_id", Integer, ForeignKey("instrument.id")),
    Column("exercise_id", Integer, ForeignKey("exercise.id")),
)

instrument_business_table = Table(
    "instrument_business",
    Base.metadata,
    Column("instrument_id", Integer, ForeignKey("instrument.id")),
    Column("business_id", Integer, ForeignKey("business.id")),
)


class InstrumentModel(Base):
    """
    This models the 'instrument' table which keeps the stored collection instruments
    """

    __tablename__ = "instrument"

    id = Column(Integer, primary_key=True, autoincrement=True)
    type = Column(String(8))
    instrument_id = Column(UUID, unique=True, index=True)
    stamp = Column(TIMESTAMP)
    survey_id = Column(Integer, ForeignKey("survey.id"))
    classifiers = Column(JSONB)
    survey = relationship("SurveyModel", back_populates="instruments")
    # Use eager loading using 'lazy="joined"' to preload SEFT information to speed up looping over the instruments. For
    # example adding this speeds up calling 'validate_non_duplicate_instrument'
    seft_file = relationship(
        "SEFTModel", uselist=False, back_populates="instrument", cascade="all, delete-orphan", lazy="joined"
    )

    exercises = relationship("ExerciseModel", secondary=instrument_exercise_table, back_populates="instruments")
    businesses = relationship(
        "BusinessModel",
        secondary=instrument_business_table,
        back_populates="instruments",
        single_parent=True,
        cascade="all, delete-orphan",
    )

    def __init__(self, classifiers=None, ci_type=None):
        """Initialise the class with optionally supplied defaults"""
        self.stamp = datetime.now()
        self.instrument_id = uuid4()
        self.classifiers = classifiers
        self.type = ci_type

    @property
    def json(self):
        return {
            "id": self.instrument_id,
            "file_name": self.name,
            "len": self.seft_file.len if self.seft_file else None,
            "stamp": self.stamp,
            "survey": self.survey.survey_id,
            "businesses": self.rurefs,
            "exercises": self.exids,
            "classifiers": self.classifiers,
            "type": self.type,
        }

    @property
    def rurefs(self):
        return [business.ru_ref for business in self.businesses]

    @property
    def exids(self):
        return [exercise.exercise_id for exercise in self.exercises]

    @property
    def name(self):
        if self.seft_file:
            return self.seft_file.file_name

        return self.classifiers.get("form_type")


class BusinessModel(Base):
    """
    This models the 'business' table which is a placeholder for the RU code
    """

    __tablename__ = "business"

    id = Column(Integer, primary_key=True)
    ru_ref = Column(String(32), index=True)
    instruments = relationship("InstrumentModel", secondary=instrument_business_table, back_populates="businesses")

    def __init__(self, ru_ref=None):
        """Initialise the class with optionally supplied defaults"""
        self.ru_ref = ru_ref

    @property
    def json(self):
        return {
            "id": self.id,
            "ru_ref": self.ru_ref,
            "instruments": self.instrument_ids,
        }

    @property
    def instrument_ids(self):
        return [instrument.id for instrument in self.instruments]


class ExerciseModel(Base):
    """
    This models the 'exercise' table which keeps the stored collection instruments
    """

    __tablename__ = "exercise"

    id = Column(Integer, primary_key=True)
    exercise_id = Column(UUID, index=True)
    instruments = relationship(
        "InstrumentModel",
        secondary=instrument_exercise_table,
        back_populates="exercises",
    )

    def __init__(self, exercise_id=None):
        """Initialise the class with optionally supplied defaults"""
        self.exercise_id = exercise_id

    @property
    def json(self):
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "instruments": self.instrument_ids,
        }

    @property
    def instrument_ids(self):
        return [instrument.id for instrument in self.instruments]

    @property
    def seft_instrument_in_exercise(self):
        return any(instrument.type == "SEFT" for instrument in self.instruments)


class SurveyModel(Base):
    """
    This models the 'business' table which is a placeholder for the RU code
    """

    __tablename__ = "survey"

    id = Column(Integer, primary_key=True)
    survey_id = Column(UUID, index=True)
    instruments = relationship("InstrumentModel", back_populates="survey")

    def __init__(self, survey_id=None):
        """Initialise the class with optionally supplied defaults"""
        self.survey_id = survey_id


class SEFTModel(Base):
    """
    This models the 'seft_instrument' table which keeps the stored seft collection instruments
    This table can be deleted once the SEFT CIs are migrated over to the bucket from the database
    """

    __tablename__ = "seft_instrument"

    id = Column(Integer, primary_key=True)
    file_name = Column(String(32))
    len = Column(Integer)
    instrument_id = Column(UUID, ForeignKey("instrument.instrument_id"))

    instrument = relationship("InstrumentModel", back_populates="seft_file")

    def __init__(self, instrument_id=None, file_name=None, length=None, data=None):
        """Initialise the class with optionally supplied defaults"""
        self.instrument_id = instrument_id
        self.file_name = file_name
        self.len = length


class RegistryInstrumentModel(Base):
    """This models the 'registry_instrument' table which holds the CIR instrument versions
    selected by the Rops user for each EQ classifier for a given collection exercise.

    * Keyed on the exercise_id, classifier_type and classifier_value, so for any given exercise_id, there can be
      only one form_type classifier for a given classifier_value
    * We currently only support "classifier_type": "form_type" (e.g. where "classifier_value" is "0001")
    * The registry_instrument will only support a single classifier (as text)
      and not multiple classifier combinations (as json)
    * In RASRM the survey_id is a UUID, however in the context of the CIR object being returned, their survey_id is
      what we know of as the three digit survey_ref e.g. "139". This table will hold OUR survey_id as a UUID and
      not the three digit survey_ref returned by the CIR API.
    """

    __tablename__ = "registry_instrument"

    # survey_id = Column(UUID, ForeignKey("survey.survey_id"))
    # exercise_id = Column(UUID, ForeignKey("exercise.exercise_id"), primary_key=True)
    # instrument_id = Column(UUID, ForeignKey("instrument.instrument_id"))
    survey_id = Column(UUID, nullable=False)
    exercise_id = Column(UUID, primary_key=True)
    instrument_id = Column(UUID, nullable=False)
    classifier_type = Column(String, primary_key=True)
    classifier_value = Column(String, primary_key=True)
    ci_version = Column(Integer, nullable=False)
    guid = Column(UUID, nullable=False)
    published_at = Column(TIMESTAMP, nullable=False)

    def __init__(
        self,
        survey_id=None,
        exercise_id=None,
        instrument_id=None,
        classifier_type=None,
        classifier_value=None,
        ci_version=None,
        guid=None,
        published_at=None,
    ):
        """Initialise the class with optionally supplied defaults"""
        self.survey_id = survey_id
        self.exercise_id = exercise_id
        self.instrument_id = instrument_id
        self.classifier_type = classifier_type
        self.classifier_value = classifier_value
        self.ci_version = ci_version
        self.guid = guid
        self.published_at = published_at

    def to_dict(self) -> dict:
        return {
            "survey_id": self.survey_id,
            "exercise_id": self.exercise_id,
            "instrument_id": self.instrument_id,
            "classifier_type": self.classifier_type,
            "classifier_value": self.classifier_value,
            "ci_version": self.ci_version,
            "guid": self.guid,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }
