from unittest import TestCase
from unittest.mock import MagicMock, patch

from application.controllers.registry_instrument import RegistryInstrument
from application.exceptions import RasError

EXERCISE_ID = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"


class TestRegistryInstrumentController(TestCase):

    @patch("application.controllers.registry_instrument.query_registry_instruments_by_exercise_id")
    def test_get_registry_instruments_by_exercise_id_returns_list_of_dicts(self, mock_query):
        session = MagicMock()

        mock_registry_instrument1 = MagicMock()
        mock_registry_instrument1.to_dict.return_value = {"dummy_key": "dummy_value_1"}

        mock_registry_instrument2 = MagicMock()
        mock_registry_instrument2.to_dict.return_value = {"dummy_key": "dummy_value_2"}

        mock_query.return_value = [mock_registry_instrument1, mock_registry_instrument2]

        controller = RegistryInstrument()
        exercise_id = EXERCISE_ID

        result = controller.get_by_exercise_id.__wrapped__(controller, exercise_id, session)

        mock_query.assert_called_once()

        self.assertEqual(result, [{"dummy_key": "dummy_value_1"}, {"dummy_key": "dummy_value_2"}])

    @patch("application.controllers.registry_instrument.query_registry_instruments_by_exercise_id")
    def test_get_registry_instruments_by_exercise_id_throws_exception_when_uuid_invalid(self, mock_query):
        session = MagicMock()

        controller = RegistryInstrument()
        exercise_id = "invalid_uuid"

        with self.assertRaises(RasError) as context:
            controller.get_by_exercise_id.__wrapped__(controller, exercise_id, session)

        self.assertEqual(context.exception.errors[0], "Value is not a valid UUID (invalid_uuid)")

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_get_registry_instrument_by_exercise_id_and_formtype_returns_dict(self, mock_query):
        session = MagicMock()

        mock_registry_instrument = MagicMock()
        mock_registry_instrument.to_dict.return_value = {"dummy_key": "dummy_value_1"}
        mock_query.return_value.first.return_value = mock_registry_instrument

        controller = RegistryInstrument()
        exercise_id = EXERCISE_ID
        formtype = "0001"

        result = controller.get_by_exercise_id_and_formtype.__wrapped__(controller, exercise_id, formtype, session)

        mock_query.assert_called_once()
        self.assertEqual(result, {"dummy_key": "dummy_value_1"})

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_get_registry_instrument_by_exercise_id_and_formtype_returns_none(self, mock_query):
        session = MagicMock()

        mock_registry_instrument = MagicMock()
        mock_query.return_value.first.return_value = None

        controller = RegistryInstrument()
        exercise_id = EXERCISE_ID
        formtype = "0001"

        result = controller.get_by_exercise_id_and_formtype.__wrapped__(controller, exercise_id, formtype, session)

        mock_query.assert_called_once()
        mock_registry_instrument.to_dict.assert_not_called()
        self.assertEqual(result, None)

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    @patch("application.controllers.registry_instrument.RegistryInstrumentModel")
    def test_save_new_registry_instrument_for_exercise_id_and_formtype(
        self, mock_registry_instrument_model, mock_query
    ):
        session = MagicMock()

        # Mock a registry instrument as NOT in the database
        mock_query.return_value.first.return_value = None

        # Set up the validated data from the posted payload
        ci_version = 99
        form_type = "0002"
        exercise_id = EXERCISE_ID
        guid = "678a583a-87f6-4c57-9f5b-12c5ced30c1e"
        published_at = "2028-01-30T12:00:00"
        survey_id = "0b1f8376-28e9-4884-bea5-acf9d709464e"
        instrument_id = "77c1e406-716a-488d-bfc9-b5b988fbaccf"

        controller = RegistryInstrument()

        result = controller.save_for_exercise_id_and_formtype.__wrapped__(
            controller, survey_id, exercise_id, instrument_id, form_type, ci_version, published_at, guid, session
        )

        # Assert that a new instrument was created and saved
        mock_query.assert_called_once()
        mock_registry_instrument_model.assert_called_once()
        self.assertEqual(mock_registry_instrument_model.return_value.ci_version, ci_version)
        self.assertEqual(mock_registry_instrument_model.return_value.guid, guid)
        self.assertEqual(mock_registry_instrument_model.return_value.published_at, published_at)
        self.assertEqual(mock_registry_instrument_model.return_value.classifier_type, "form_type")
        self.assertEqual(mock_registry_instrument_model.return_value.survey_id, survey_id)
        self.assertEqual(mock_registry_instrument_model.return_value.exercise_id, exercise_id)
        self.assertEqual(mock_registry_instrument_model.return_value.instrument_id, instrument_id)
        self.assertEqual(mock_registry_instrument_model.return_value.classifier_value, form_type)
        self.assertEqual(result, (True, True))
        session.add.assert_called_once()

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_save_existing_registry_instrument_for_exercise_id_and_formtype(self, mock_query):
        session = MagicMock()

        # Mock the existing registry instrument already in the database
        mock_registry_instrument = MagicMock()
        mock_registry_instrument.to_dict.return_value = {
            "ci_version": 3,
            "guid": "ac3c5a3a-2ebb-47dc-9727-22c473086a82",
            "published_at": "2025-12-31T12:00:00",
        }
        mock_query.return_value.first.return_value = mock_registry_instrument

        # Set up the validated data from the posted payload
        ci_version = 99
        form_type = "0002"
        exercise_id = EXERCISE_ID
        guid = "678a583a-87f6-4c57-9f5b-12c5ced30c1e"
        published_at = "2028-01-30T12:00:00"

        controller = RegistryInstrument()

        result = controller.save_for_exercise_id_and_formtype.__wrapped__(
            controller, None, exercise_id, None, form_type, ci_version, published_at, guid, session
        )

        # Assert that the existing instrument was updated and saved
        mock_query.assert_called_once()
        self.assertEqual(result, (True, False))
        self.assertEqual(mock_registry_instrument.ci_version, 99)
        self.assertEqual(mock_registry_instrument.guid, "678a583a-87f6-4c57-9f5b-12c5ced30c1e")
        self.assertEqual(mock_registry_instrument.published_at, "2028-01-30T12:00:00")
        session.add.assert_called_once()

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_delete_existing_registry_instrument_by_exercise_id_and_formtype(self, mock_query):
        session = MagicMock()

        form_type = "0002"
        exercise_id = EXERCISE_ID

        # Mock the existing registry instrument to be deleted
        mock_registry_instrument = MagicMock()
        mock_query.return_value.first.return_value = mock_registry_instrument

        controller = RegistryInstrument()

        result = controller.delete_by_exercise_id_and_formtype.__wrapped__(controller, exercise_id, form_type, session)

        mock_query.assert_called_once()
        self.assertEqual(result, True)
        session.delete.assert_called_once()

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_delete_non_existent_registry_instrument_by_exercise_id_and_formtype(self, mock_query):
        session = MagicMock()

        form_type = "0002"
        exercise_id = EXERCISE_ID

        # Mock the non-existent registry instrument to be deleted
        mock_query.return_value.first.return_value = None

        controller = RegistryInstrument()

        result = controller.delete_by_exercise_id_and_formtype.__wrapped__(controller, exercise_id, form_type, session)

        mock_query.assert_called_once()
        self.assertEqual(result, False)
        session.delete.assert_not_called()

    def test_count_by_exercise_id(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = 1

        controller = RegistryInstrument()
        result = controller.get_count_by_exercise_id.__wrapped__(controller, EXERCISE_ID, session)

        self.assertEqual(result, {"registry_instrument_count": 1})

    def test_count_by_exercise_id_no_instruments(self):
        session = MagicMock()
        session.execute.return_value.first.return_value = None

        controller = RegistryInstrument()
        result = controller.get_count_by_exercise_id.__wrapped__(controller, EXERCISE_ID, session)

        self.assertEqual(result, {"registry_instrument_count": 0})
