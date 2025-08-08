import json
from unittest import TestCase
from unittest.mock import MagicMock, patch

import requests_mock
from google.cloud.exceptions import NotFound

from application.controllers.collection_instrument import (
    COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED,
    COLLECTION_EXERCISE_NOT_FOUND_IN_DB,
    COLLECTION_EXERCISE_NOT_FOUND_ON_GCP,
    CollectionInstrument,
)
from application.controllers.registry_instrument import RegistryInstrument
from application.controllers.session_decorator import with_db_session
from application.exceptions import RasDatabaseError, RasError
from application.models.models import (
    BusinessModel,
    ExerciseModel,
    InstrumentModel,
    RegistryInstrumentModel,
    SEFTModel,
    SurveyModel,
)
from tests.test_client import TestClient

TEST_FILE_LOCATION = "tests/files/test.xlsx"
COLLECTION_EXERCISE_ID = "db0711c3-0ac8-41d3-ae0e-567e5ea1ef87"


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
        self.instrument_id = self._add_instrument_data()

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

    @patch("application.controllers.collection_instrument.GoogleCloudSEFTCIBucket")
    @requests_mock.mock()
    def test_delete_seft_collection_instrument(self, mock_bucket, mock_request):
        mock_bucket.delete_file_from_bucket.return_value = True
        self._mock_survey_service_request(mock_request)
        seft_instrument_id = str(self.instrument_id)
        self.collection_instrument.delete_collection_instrument(seft_instrument_id)
        instrument = self.collection_instrument.get_instrument_json(seft_instrument_id)

        self.assertEqual(instrument, None)

    def test_delete_collection_instrument_not_found(self):
        with self.assertRaises(RasError) as error:
            self.collection_instrument.delete_collection_instrument("8b4a214b-466b-4882-90a1-fe90ad59e2fc")

        self.assertEqual(404, error.exception.status_code)
        self.assertEqual(
            ["Collection instrument 8b4a214b-466b-4882-90a1-fe90ad59e2fc not found"],
            error.exception.errors,
        )

    def test_delete_eq_collection_instrument(self):
        eq_collection_instrument_id = self._add_instrument_data(ci_type="EQ")
        self.collection_instrument.delete_collection_instrument(str(eq_collection_instrument_id))
        instrument = self.collection_instrument.get_instrument_json(str(eq_collection_instrument_id))
        self.assertEqual(instrument, None)

    @patch("application.models.google_cloud_bucket.storage")
    @requests_mock.mock()
    def test_delete_collection_instruments_by_exercise_seft(self, mock_storage, mock_request):
        # Given a SEFT instrument and exercise are added at setup
        # When delete_collection_instruments_by_exercise is called with the relevant collection exercise id
        self._mock_survey_service_request(mock_request)
        message, status = self.collection_instrument.delete_collection_instruments_by_exercise(COLLECTION_EXERCISE_ID)

        # Then the exercise is deleted in the DB and on GCP
        self.assertEqual(self._query_exercise_by_id(COLLECTION_EXERCISE_ID), None)
        mock_storage.Client().bucket().delete_blobs.assert_called()
        self.assertEqual(message, COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED)
        self.assertEqual(status, 200)

    @patch("application.models.google_cloud_bucket.storage")
    @requests_mock.mock()
    def test_delete_collection_instruments_by_exercise_eq_and_seft(self, mock_storage, mock_request):
        # Given a SEFT instrument and exercise are added at setup, and an EQ instrument added to the exercise
        self._mock_survey_service_request(mock_request)
        self._add_instrument_to_exercise(ci_type="EQ", exercise_id=COLLECTION_EXERCISE_ID)

        # When delete_collection_instruments_by_exercise is called with the relevant collection exercise id
        message, status = self.collection_instrument.delete_collection_instruments_by_exercise(COLLECTION_EXERCISE_ID)

        # Then the exercise is deleted in the DB and on GCP
        self.assertEqual(self._query_exercise_by_id(COLLECTION_EXERCISE_ID), None)
        self.assertEqual(message, COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED)
        mock_storage.Client().bucket().delete_blobs.assert_called()
        self.assertEqual(status, 200)

    @patch("application.models.google_cloud_bucket.storage")
    def test_delete_collection_instruments_by_exercise_eq(self, mock_storage):
        # Given a EQ instrument and exercise are added
        eq_collection_exercise_id = "901e837a-b3b7-420d-a5ab-7518f6868973"
        self._add_instrument_data(ci_type="EQ", exercise_id=eq_collection_exercise_id)

        # When delete_collection_instruments_by_exercise is called with the relevant collection exercise id
        message, status = self.collection_instrument.delete_collection_instruments_by_exercise(
            eq_collection_exercise_id
        )
        # Then the exercise is deleted in the DB but not on GCP (eQ's don't have CIs on GCP)
        self.assertEqual(self._query_exercise_by_id(eq_collection_exercise_id), None)
        self.assertEqual(message, COLLECTION_EXERCISE_AND_ASSOCIATED_FILES_DELETED)
        mock_storage.Client().bucket().delete_blobs.assert_not_called()
        self.assertEqual(status, 200)

    def test_delete_collection_instruments_by_exercise_not_found_db(self):
        # Given a collection exercise that doesn't exist in the db
        incorrect_ce_id = "228f41a1-8e65-4327-b579-6c531c7f97a3"

        # When delete_collection_instruments_by_exercise is called with the relevant collection exercise id
        message, status = self.collection_instrument.delete_collection_instruments_by_exercise(incorrect_ce_id)

        # Then a 404 is returned with the correct message
        self.assertEqual(message, COLLECTION_EXERCISE_NOT_FOUND_IN_DB)
        self.assertEqual(status, 404)

    @patch("application.models.google_cloud_bucket.storage")
    @requests_mock.mock()
    def test_delete_collection_instruments_by_exercise_not_found_gcp(self, mock_storage, mock_request):
        # Given a collection exercise id that doesn't exist on GCP
        self._mock_survey_service_request(mock_request)
        mock_storage.Client().bucket().delete_blobs.side_effect = NotFound("testing")

        # When delete_collection_instruments_by_exercise is called with the relevant collection exercise id
        message, status = self.collection_instrument.delete_collection_instruments_by_exercise(COLLECTION_EXERCISE_ID)

        # Then a 404 is returned with the correct message
        self.assertEqual(message, COLLECTION_EXERCISE_NOT_FOUND_ON_GCP)
        self.assertEqual(status, 404)

    def test_get_instrument_by_incorrect_id(self):
        # Given there is an instrument in the db
        # When an incorrect instrument id is used to find that instrument
        instrument = self.collection_instrument.get_instrument_json(COLLECTION_EXERCISE_ID)

        # Then that instrument is not found
        self.assertEqual(instrument, None)

    def test_update_exercise_eq_instruments_doesnt_remove_seft(self):
        # Given there is an instrument in the db for a SEFT
        # When an eQ is added to collection exercise id
        self._add_instrument_data(ci_type="EQ")

        # Then the user unselects this eQ and exercise instrument is updated
        self.collection_instrument.update_exercise_eq_instruments(COLLECTION_EXERCISE_ID, [])

        # And the eQ is removed but the SEFT is still present
        instrument = self.collection_instrument.get_instrument_json(str(self.instrument_id))

        self.assertIn(str(self.instrument_id), json.dumps(str(instrument)))
        self.assertIn("SEFT", json.dumps(str(instrument)))
        self.assertNotIn("EQ", json.dumps(str(instrument)))

    def test_update_exercise_eq_instruments_remove_registry_instrument(self):
        # Given there is a collection and registry instrument
        instrument_id = self._add_instrument_data(ci_type="EQ")
        self._add_registry_instrument(instrument_id)

        # when the user unselects and updates the collection instrument
        self.collection_instrument.update_exercise_eq_instruments(COLLECTION_EXERCISE_ID, [])
        registry_instrument = RegistryInstrument().get_by_exercise_id_and_formtype(COLLECTION_EXERCISE_ID, "0001")

        # Then the registry_instrument is deleted
        self.assertIsNone(registry_instrument)

    @with_db_session
    def _add_instrument_data(self, session=None, ci_type="SEFT", exercise_id=COLLECTION_EXERCISE_ID):
        instrument = InstrumentModel(ci_type=ci_type)
        exercise = ExerciseModel(exercise_id=exercise_id)
        instrument.exercises.append(exercise)
        if ci_type == "SEFT":
            self._add_seft_details(instrument)
        survey = SurveyModel(survey_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87")
        instrument.survey = survey
        session.add(instrument)
        return instrument.instrument_id

    @with_db_session
    def _add_registry_instrument(self, instrument_id, session=None):
        registry_instrument = RegistryInstrumentModel(
            survey_id="cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            exercise_id=COLLECTION_EXERCISE_ID,
            instrument_id=instrument_id,
            classifier_type="form_type",
            classifier_value="0001",
            ci_version=1,
            guid="9579fa25-d150-4566-9569-5c2ffabd787f",
            published_at="Thu, 07 Aug 2025 15:19:33 +0000",
        )

        session.add(registry_instrument)

    @staticmethod
    def _add_seft_details(instrument):
        seft_file = SEFTModel(instrument_id=instrument.instrument_id, file_name="test_file")
        business = BusinessModel(ru_ref="test_ru_ref")
        instrument.seft_file = seft_file
        instrument.businesses.append(business)

    @with_db_session
    def _add_instrument_to_exercise(self, session=None, ci_type="EQ", exercise_id=COLLECTION_EXERCISE_ID):
        instrument = InstrumentModel(ci_type=ci_type)
        exercise = self._query_exercise_by_id(exercise_id)
        instrument.exercises.append(exercise)
        if ci_type == "SEFT":
            self._add_seft_details(instrument)
        session.add(instrument)

    @staticmethod
    @with_db_session
    def _query_exercise_by_id(exercise_id, session):
        return session.query(ExerciseModel).filter(ExerciseModel.exercise_id == exercise_id).first()

    @staticmethod
    def _mock_survey_service_request(mock_request):
        mock_request.get(
            "http://localhost:8080/surveys/cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87",
            status_code=200,
            json={"surveyId": "cb0711c3-0ac8-41d3-ae0e-567e5ea1ef87", "surveyRef": "139"},
        )
