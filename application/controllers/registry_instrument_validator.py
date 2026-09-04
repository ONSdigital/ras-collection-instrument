import datetime
import re

from application.controllers.helper import validate_uuid

EXPECTED_KEYS = {
    "survey_id",
    "exercise_id",
    "instrument_id",
    "classifier_type",
    "classifier_value",
    "ci_version",
    "guid",
    "published_at",
}


def validate_registry_instrument_payload(payload, exercise_id):
    payload_keys = set(payload.keys())

    if payload_keys != EXPECTED_KEYS:
        return False, f"Invalid payload keys. Expected: {EXPECTED_KEYS}"
    if payload["exercise_id"] != exercise_id:
        return False, "exercise_id in payload does not match path parameter"

    validate_uuid(payload["survey_id"])
    validate_uuid(payload["exercise_id"])
    validate_uuid(payload["instrument_id"])
    validate_uuid(payload["guid"])

    if payload["classifier_type"] not in ["form_type"]:
        return False, "Invalid classifier type"
    if not re.fullmatch(r"\d{4}", str(payload["classifier_value"])):
        return False, "Invalid classifier value"
    try:
        int(payload["ci_version"])
    except (ValueError, TypeError):
        return False, "Invalid ci_version"
    try:
        datetime.datetime.fromisoformat(payload["published_at"])
    except (ValueError, TypeError):
        return False, "Invalid published_at"
    return True, None
