import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests_mock

from application.controllers.collection_instrument import CollectionInstrument
from application.controllers.session_decorator import with_db_session
from application.exceptions import RasDatabaseError, RasError
from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
    SEFTModel,
    SurveyModel,
)
from application.views.collection_instrument_view import (
    publish_uploaded_collection_instrument,
)
from tests.test_client import TestClient

TEST_FILE_LOCATION = "tests/files/test.xlsx"
url_collection_instrument_link_url = "http://localhost:8145/collection-instrument/link"


class TestCollectionInstrumentUnit(TestCase):
    instrument_id = "5f023a96-fdcd-4177-8036-7d13878465eb"
    file = ""

    def test_patch_seft_instrument_invalid_uuid(self):
        test_input = "not-a-uuid"
        session = MagicMock()
        instrument = CollectionInstrument()

        with self.assertRaises(RasError) as error:
            instrument.patch_seft_instrument.__wrapped__(instrument, test_input, self.file, session)

        expected = [f"Value is not a valid UUID ({test_input})"]
        expected_status = 400
        self.assertEqual(expected, error.exception.errors)
        self.assertEqual(expected_status, error.exception.status_code)

    @patch("application.controllers.collection_instrument.CollectionInstrument.get_instrument_by_id")
    def test_patch_seft_instrument_instrument_not_found(self, get_instrument):
        get_instrument.return_value = None
        session = MagicMock()
        instrument = CollectionInstrument()

        with self.assertRaises(RasError) as error:
            instrument.patch_seft_instrument.__wrapped__(instrument, self.instrument_id, self.file, session)

        expected = ["Instrument not found"]
        expected_status = 400
        self.assertEqual(expected, error.exception.errors)
        self.assertEqual(expected_status, error.exception.status_code)

    @patch("application.controllers.collection_instrument.CollectionInstrument.get_instrument_by_id")
    def test_patch_seft_instrument_instrument_not_seft(self, get_instrument):
        instrument_model = InstrumentModel()
        instrument_model.type = "EQ"
        get_instrument.return_value = instrument_model
        session = MagicMock()
        instrument = CollectionInstrument()

        with self.assertRaises(RasError) as error:
            instrument.patch_seft_instrument.__wrapped__(instrument, self.instrument_id, self.file, session)

        expected = ["Not a SEFT instrument"]
        expected_status = 400
        self.assertEqual(expected, error.exception.errors)
        self.assertEqual(expected_status, error.exception.status_code)


class TestCollectionInstrument(TestClient):
    """Collection Instrument unit tests"""

    def setUp(self):
        self.collection_instrument = CollectionInstrument()
        self.instrument_id = self.add_instrument_data()

    def test_get_instrument_by_search_string_collection_exercise_id(self):
        # Given there is an instrument in the db
        # When a collection exercise id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_by_search_string(
            '{"COLLECTION_EXERCISE": "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        )

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_survey_id(self):
        # Given there is an instrument in the db
        # When the survey id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_by_search_string(
            '{"SURVEY_ID": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87"}'
        )

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_type(self):
        # Given there is an instrument in the db
        # When the type is used to find that instrument
        instrument = self.collection_instrument.get_instrument_by_search_string('{"TYPE": "SEFT"}')

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_empty_search(self):
        # Given there is an instrument in the db
        # When an empty search string is used
        instrument = self.collection_instrument.get_instrument_by_search_string()

        # Then that instrument is returned
        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))

    def test_get_instrument_by_search_string_invalid_search_value(self):
        # Given that a valid classifier is used but with an invalid value (should be uuid)
        # When the function is called
        # Than a RasDatabaseError is raised
        with self.assertRaises(RasDatabaseError):
            self.collection_instrument.get_instrument_by_search_string('{"COLLECTION_EXERCISE": "invalid_uuid"}')

    def test_get_instrument_by_incorrect_id(self):
        # Given there is an instrument in the db
        # When an incorrect instrument id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_json("db0711c3-0ac8-41d3-ae0e-567e5ea1ef87")

        # Then that instrument is not found
        self.assertEqual(instrument, None)

    @requests_mock.mock()
    def test_publish_uploaded_collection_instrument(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=200)
        # Given there is an instrument in the db
        # When publishing to a rabbit exchange that a collection instrument has been uploaded
        c_id = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
        result = publish_uploaded_collection_instrument(c_id, self.instrument_id)

        # Then the message is successfully published
        self.assertEqual(result.status_code, 200)

    @requests_mock.mock()
    def test_publish_uploaded_collection_instrument_rabbit_fails(self, mock_request):
        mock_request.post(url_collection_instrument_link_url, status_code=500)
        # Given there is an instrument in the db
        # When publishing to a rabbit exchange that a collection instrument has been uploaded
        c_id = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"
        with self.assertRaises(Exception):
            publish_uploaded_collection_instrument(c_id, self.instrument_id)

    @staticmethod
    @with_db_session
    def add_instrument_data(session=None):
        instrument = InstrumentModel(ci_type="SEFT")
        seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name="test_file")
        exercise = ExerciseModel(exercise_id="db0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        business = BusinessModel(ru_ref="test_ru_ref")
        instrument.seft_file = seft_file
        instrument.exercises.append(exercise)
        instrument.businesses.append(business)
        survey = SurveyModel(survey_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id
