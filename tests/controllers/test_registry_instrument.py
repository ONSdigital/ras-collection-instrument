from unittest import TestCase
from unittest.mock import MagicMock, patch

from application.controllers.registry_instrument import RegistryInstrument
from application.exceptions import RasError


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
        exercise_id = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"

        result = controller.get_registry_instruments_by_exercise_id.__wrapped__(controller, exercise_id, session)

        mock_query.assert_called_once()

        self.assertEqual(result, [{"dummy_key": "dummy_value_1"}, {"dummy_key": "dummy_value_2"}])
        mock_registry_instrument1.to_dict.assert_called_once()
        mock_registry_instrument2.to_dict.assert_called_once()

    @patch("application.controllers.registry_instrument.query_registry_instruments_by_exercise_id")
    def test_get_registry_instruments_by_exercise_id_throws_exception_when_uuid_invalid(self, mock_query):
        session = MagicMock()

        controller = RegistryInstrument()
        exercise_id = "invalid_uuid"

        with self.assertRaises(RasError) as context:
            controller.get_registry_instruments_by_exercise_id.__wrapped__(controller, exercise_id, session)

        self.assertEqual(context.exception.errors[0], "Value is not a valid UUID (invalid_uuid)")

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_get_registry_instrument_by_exercise_id_and_formtype_returns_dict(self, mock_query):

        session = MagicMock()

        mock_registry_instrument = MagicMock()
        mock_registry_instrument.to_dict.return_value = {"dummy_key": "dummy_value_1"}
        mock_query.return_value.first.return_value = mock_registry_instrument

        controller = RegistryInstrument()
        exercise_id = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"
        formtype = "0001"

        result = controller.get_registry_instrument_by_exercise_id_and_formtype.__wrapped__(
            controller, exercise_id, formtype, session
        )

        mock_query.assert_called_once()
        mock_registry_instrument.to_dict.assert_called_once()
        self.assertEqual(result, {"dummy_key": "dummy_value_1"})

    @patch("application.controllers.registry_instrument.query_registry_instrument_by_exercise_id_and_formtype")
    def test_get_registry_instrument_by_exercise_id_and_formtype_returns_none(self, mock_query):

        session = MagicMock()

        mock_registry_instrument = MagicMock()
        mock_query.return_value.first.return_value = None

        controller = RegistryInstrument()
        exercise_id = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"
        formtype = "0001"

        result = controller.get_registry_instrument_by_exercise_id_and_formtype.__wrapped__(
            controller, exercise_id, formtype, session
        )

        mock_query.assert_called_once()
        mock_registry_instrument.to_dict.assert_not_called()
        self.assertEqual(result, None)
