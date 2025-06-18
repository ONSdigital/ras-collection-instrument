import datetime
import unittest

from application.controllers.registry_instrument_validator import (
    validate_registry_instrument_payload,
)
from application.exceptions import RasError

VALID_UUID = "123e4567-e89b-12d3-a456-426614174000"
VALID_PAYLOAD = {
    "survey_id": VALID_UUID,
    "exercise_id": VALID_UUID,
    "instrument_id": VALID_UUID,
    "classifier_type": "form_type",
    "classifier_value": "0001",
    "ci_version": 99,
    "guid": VALID_UUID,
    "published_at": datetime.datetime.now().isoformat(),
}


class TestValidateRegistryInstrumentPayload(unittest.TestCase):
    def test_valid_payload(self):
        is_valid, error = validate_registry_instrument_payload(VALID_PAYLOAD, VALID_UUID)
        self.assertTrue(is_valid)
        self.assertIsNone(error)

    def test_invalid_keys(self):
        payload = VALID_PAYLOAD.copy()
        payload.pop("guid")
        is_valid, error = validate_registry_instrument_payload(payload, VALID_UUID)
        self.assertFalse(is_valid)
        self.assertIn("Invalid payload keys", error)

    def test_mismatched_exercise_id(self):
        is_valid, error = validate_registry_instrument_payload(VALID_PAYLOAD, "different-id")
        self.assertFalse(is_valid)
        self.assertIn("does not match path parameter", error)

    def test_invalid_uuids(self):
        for key in ["survey_id", "exercise_id", "instrument_id", "guid"]:
            payload = VALID_PAYLOAD.copy()
            payload[key] = "invalid_uuid"
            try:
                validate_registry_instrument_payload(payload, VALID_UUID)
            except RasError as e:
                self.assertIn("Value is not a valid UUID (invalid_uuid)", e.errors[0])

    def test_invalid_classifier_type(self):
        payload = VALID_PAYLOAD.copy()
        payload["classifier_type"] = "bad_type"
        is_valid, error = validate_registry_instrument_payload(payload, VALID_UUID)
        self.assertFalse(is_valid)
        self.assertIn("Invalid classifier type", error)

    def test_invalid_classifier_value(self):
        payload = VALID_PAYLOAD.copy()
        payload["classifier_value"] = "abcd"
        is_valid, error = validate_registry_instrument_payload(payload, VALID_UUID)
        self.assertFalse(is_valid)
        self.assertIn("Invalid classifier value", error)

    def test_invalid_ci_version(self):
        payload = VALID_PAYLOAD.copy()
        payload["ci_version"] = "not-an-int"
        is_valid, error = validate_registry_instrument_payload(payload, VALID_UUID)
        self.assertFalse(is_valid)
        self.assertIn("Invalid ci_version", error)

    def test_invalid_published_at(self):
        payload = VALID_PAYLOAD.copy()
        payload["published_at"] = "not-a-date"
        is_valid, error = validate_registry_instrument_payload(payload, VALID_UUID)
        self.assertFalse(is_valid)
        self.assertIn("Invalid published_at", error)
