from unittest import TestCase
from unittest.mock import MagicMock, patch

from application.controllers.registry_instrument import RegistryInstrument


class TestRegistryInstrumentController(TestCase):

    @patch("application.controllers.registry_instrument.query_registry_instruments_by_exercise_id")
    @patch("application.controllers.registry_instrument.validate_uuid")
    def test_get_registry_instruments_by_exercise_id_returns_list_of_dicts(self, mock_validate_uuid, mock_query):

        session = MagicMock()

        mock_registry_instrument1 = MagicMock()
        mock_registry_instrument1.to_dict.return_value = {"dummy_key": "dummy_value_1"}

        mock_registry_instrument2 = MagicMock()
        mock_registry_instrument2.to_dict.return_value = {"dummy_key": "dummy_value_2"}

        mock_query.return_value = [mock_registry_instrument1, mock_registry_instrument2]

        controller = RegistryInstrument()
        exercise_id = "3ff59b73-7f15-406f-9e4d-7f00b41e85ce"

        result = controller.get_registry_instruments_by_exercise_id.__wrapped__(controller, exercise_id, session)

        mock_validate_uuid.assert_called_once_with(exercise_id)
        mock_query.assert_called_once()

        self.assertEqual(result, [{"dummy_key": "dummy_value_1"}, {"dummy_key": "dummy_value_2"}])
        mock_registry_instrument1.to_dict.assert_called_once()
        mock_registry_instrument2.to_dict.assert_called_once()
