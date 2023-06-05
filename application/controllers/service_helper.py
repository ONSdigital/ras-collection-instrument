import logging

import requests
import structlog
from flask import current_app

from application.exceptions import RasError, ServiceUnavailableException

log = structlog.wrap_logger(logging.getLogger(__name__))


def get_survey_details(survey_id):
    """
    :param survey_id: The survey_id UUID to search with
    :return: survey reference
    """
    response = service_request(service="survey-service", endpoint="surveys", search_value=survey_id)
    return response.json()


def service_request(service, endpoint, search_value):
    """
    Makes a request to a different micro service

    :param service: The micro service to call to
    :param endpoint: The end point of the micro service
    :param search_value: The value to search on
    :return: response
    """

    auth = (current_app.config.get("SECURITY_USER_NAME"), current_app.config.get("SECURITY_USER_PASSWORD"))

    try:
        service_root = {
            "survey-service": current_app.config["SURVEY_URL"],
            "collectionexercise-service": current_app.config["COLLECTION_EXERCISE_URL"],
            "case-service": current_app.config["CASE_URL"],
            "party-service": current_app.config["PARTY_URL"],
        }[service]
        service_url = f"{service_root}/{endpoint}/{search_value}"
        log.info(f"Making request to {service_url}")
    except KeyError:
        raise RasError(f"service '{service}' not configured", 500)

    try:
        response = requests.get(service_url, auth=auth)
        response.raise_for_status()
    except requests.HTTPError:
        raise RasError(f"{service} returned a HTTPError")
    except requests.ConnectionError:
        raise ServiceUnavailableException(f"{service} returned a connection error", 503)
    except requests.Timeout:
        raise ServiceUnavailableException(f"{service} has timed out", 504)
    return response


def collection_exercise_instrument_update_request(exercise_id: str) -> object:
    """
    Posts a request to the collection exercise service to notify of a collection instrument change
    :param: json_message
    :type: json
    :return: response
    """

    auth = (current_app.config.get("SECURITY_USER_NAME"), current_app.config.get("SECURITY_USER_PASSWORD"))

    try:
        collection_exercise_url = current_app.config["COLLECTION_EXERCISE_URL"]
        url = f"{collection_exercise_url}/collection-instrument/link"
        log.info("Making request to collection exercise to acknowledge instruments have changed")
        response = requests.post(url, json={"exercise_id": str(exercise_id)}, auth=auth)
        response.raise_for_status()
    except KeyError:
        raise RasError("collection exercise service not configured", 500)
    except requests.HTTPError:
        raise RasError("collection exercise responded with an http error", response.status_code)

    return response
