import logging
from typing import Any

import requests
import structlog
from flask import current_app

from application.exceptions import RasError, ServiceUnavailableException
from application.oidc.oidc import OIDCCredentialsService

log = structlog.wrap_logger(logging.getLogger(__name__))


def collection_exercise_instrument_update_request(action, exercise_id: str) -> object:
    """
    Posts a request to the collection exercise service to notify of a collection instrument change
    :param: json_message
    :type: json
    :return: response
    """
    json_message = {"action": action, "exercise_id": str(exercise_id)}

    try:
        collection_exercise_url = current_app.config["COLLECTION_EXERCISE_URL"]
        url = f"{collection_exercise_url}/collection-instrument/link"
        log.info("Making request to collection exercise to acknowledge instruments have been changed", action=action)
        response = requests.post(url, json=json_message, auth=_get_auth())
        response.raise_for_status()
    except KeyError:
        raise RasError("collection exercise service not configured", 500)
    except requests.HTTPError:
        raise RasError("collection exercise responded with an http error", response.status_code)

    return response


def get_collection_exercise_by_id(exercise_id: str) -> dict[str, Any]:
    url = f"{current_app.config['COLLECTION_EXERCISE_URL']}" f"/collectionexercises/{exercise_id}"
    return _get_json(url, "collection exercise", auth=_get_auth())


def get_survey_details_by_id(survey_id: str) -> dict[str, Any]:
    url = f"{current_app.config['SURVEY_URL']}" f"/surveys/{survey_id}"
    return _get_json(url, "survey", auth=_get_auth())


def get_collection_exercise_id_by_period_and_survey_ref(period_ref: str, survey_ref: str) -> str:
    url = f"{current_app.config['COLLECTION_EXERCISE_URL']}" f"/collectionexercises/{period_ref}/survey/{survey_ref}"

    try:
        response = _get_json(url, "collection exercise", auth=_get_auth())
    except RasError as error:
        if error.status_code == 404:
            log.info(f"Collection exercise not found for survey {survey_ref} and period {period_ref}")
            raise ValueError("Collection exercise not found") from error
        raise
    return response["id"]


def get_cir_metadata(form_type: str, survey_ref: str) -> list[dict[str, Any]]:
    session = requests.Session()
    fetch_and_apply_oidc_credentials(
        session=session,
        client_id=current_app.config["CIR_OAUTH2_CLIENT_ID"],
    )
    url = current_app.config["CIR_API_URL"] + current_app.config["CIR_API_PREFIX"]
    params = {
        "classifier_type": "form_type",
        "classifier_value": form_type,
        "language": "en",
        "survey_id": survey_ref,
    }
    return _get_json(url, "CIR", session=session, params=params)


def fetch_and_apply_oidc_credentials(session: requests.Session, client_id: str) -> None:
    oidc_credentials_service: OIDCCredentialsService = current_app.oidc["oidc_credentials_service"]
    credentials = oidc_credentials_service.get_credentials(iap_client_id=client_id)
    credentials.apply(headers=session.headers)


def _get_json(
    url: str,
    service: str,
    session: requests.Session | None = None,
    auth: tuple[str, str] | None = None,
    params: dict[str, str] | None = None,
):

    client = session or requests  # oidc uses a session to authenticate

    try:
        response = client.get(url, auth=auth, params=params)
        response.raise_for_status()

    except requests.HTTPError as e:
        raise RasError(f"{service} returned an HTTP error", e.response.status_code) from e

    except requests.ConnectionError:
        raise ServiceUnavailableException(f"{service} returned a connection error", 503)

    except requests.Timeout:
        raise ServiceUnavailableException(f"{service} timed out", 504)

    return response.json()


def _get_auth() -> tuple[str, str]:
    return (
        current_app.config["SECURITY_USER_NAME"],
        current_app.config["SECURITY_USER_PASSWORD"],
    )
