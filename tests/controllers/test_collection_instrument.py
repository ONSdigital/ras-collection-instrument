import json

from application.controllers.collection_instrument import CollectionInstrument
from application.controllers.session_decorator import with_db_session
from application.models.models import ExerciseModel, InstrumentModel, BusinessModel, SurveyModel
from application.exceptions import RasDatabaseError, RasError
from tests.test_client import TestClient


TEST_FILE_LOCATION = 'tests/files/test.xlsx'


class TestCollectionInstrument(TestClient):
    """ Collection Instrument unit tests"""

    def setUp(self):
        self.collection_instrument = CollectionInstrument()
        self.instrument_id = self.add_instrument_data()

    def test_get_instrument_by_search_string_collection_exercise_id(self):

        # Given there is an instrument in the db
        # When a collection exercise id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_by_search_string(
            '{\"COLLECTION_EXERCISE\": \"db0711c3-0ac8-41d3-ae0e-567e5ea1ef87\"}')

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_survey_id(self):
        # Given there is an instrument in the db
        # When the survey id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_by_search_string(
            '{\"SURVEY_ID\": \"cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87\"}')

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_empty_search(self):

        # Given there is an instrument in the db
        # When an empty search string is used
        instrument = self.collection_instrument.get_instrument_by_search_string()

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_invalid_search_string_classifier(self):

        # Given that an invalid classifier is used in a search string
        # When the function is called
        # Than a RasError is raised
        with self.assertRaises(RasError):
            self.collection_instrument.get_instrument_by_search_string('{\"invalid_classifier\": \"999\"}')

    def test_get_instrument_by_search_string_invalid_search_value(self):

        # Given that a valid classifier is used but with an invalid value (should be uuid)
        # When the function is called
        # Than a RasDatabaseError is raised
        with self.assertRaises(RasDatabaseError):
            self.collection_instrument.get_instrument_by_search_string('{\"COLLECTION_EXERCISE\": \"invalid_uuid\"}')

    def test_get_instrument_by_incorrect_id(self):

        # Given there is an instrument in the db
        # When an incorrect instrument id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_json('db0711c3-0ac8-41d3-ae0e-567e5ea1ef87')

        # Then that instrument is not found
        self.assertEquals(instrument, None)

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None):
        instrument = InstrumentModel()
        exercise = ExerciseModel(exercise_id='db0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        business = BusinessModel(ru_ref='test_ru_ref')
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        survey = SurveyModel(survey_id='cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87')
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id
