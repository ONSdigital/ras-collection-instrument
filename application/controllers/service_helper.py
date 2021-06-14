import logging

import requests
import structlog
from flask import current_app

from application.exceptions import RasError

log = structlog.wrap_logger(logging.getLogger(__name__))


def get_case_group(case_id):
    """
    Get case details from service
    :param case_id: The case_id to search with
    :return: case details
    """

    case_group = None
    response = service_request(service='case-service', endpoint='cases', search_value=case_id)

    if response.status_code == 200:
        case = response.json()
        case_group = case.get('caseGroup')
    else:
        log.error("Case not found", case_id=case_id)
    return case_group


def get_collection_exercise(collection_exercise_id):
    """
    Get collection exercise details from request
    :param collection_exercise_id: The collection_exercise_id to search with
    :return: collection_exercise
    """

    collection_exercise = None
    response = service_request(service='collectionexercise-service',
                               endpoint='collectionexercises',
                               search_value=collection_exercise_id)

    if response.status_code == 200:
        collection_exercise = response.json()
    else:
        log.info('Collection Exercise not found', collection_exercise_id=collection_exercise_id)
    return collection_exercise


def get_survey_ref(survey_id):
    """
    :param survey_id: The survey_id UUID to search with
    :return: survey reference
    """

    survey_ref = None
    response = service_request(service='survey-service', endpoint='surveys', search_value=survey_id)

    if response.status_code == 200:
        survey_service_data = response.json()
        survey_ref = survey_service_data.get('surveyRef')
    else:
        log.info('Survey service data not found', survey_id=survey_id)

    return survey_ref


def get_business_party(business_id, collection_exercise_id=None, verbose=False):
    """
    :param business_id: The business UUID to search with
    :param collection_exercise_id: The collection exercise id to retrieve attributes for
    :param verbose: Boolean to decide the verbosity of the party response
    :return: a business party
    """
    log.info('Retrieving business party', party_id=business_id, collection_exercise_id=collection_exercise_id)
    response = service_request(service='party-service',
                               endpoint='party-api/v1/businesses/id',
                               search_value=f'{business_id}?verbose={verbose}'
                                            f'&collection_exercise_id={collection_exercise_id}')

    if not response.ok:
        log.error('Failed to find business', party_id=business_id, collection_exercise_id=collection_exercise_id)
        return None

    log.info('Successfully retrieved business', party_id=business_id, collection_exercise_id=collection_exercise_id)
    return response.json()


def service_request(service, endpoint, search_value):
    """
    Makes a request to a different micro service

    :param service: The micro service to call to
    :param endpoint: The end point of the micro service
    :param search_value: The value to search on
    :return: response
    """

    auth = (current_app.config.get('SECURITY_USER_NAME'), current_app.config.get('SECURITY_USER_PASSWORD'))

    try:
        service = {
            'survey-service': current_app.config['SURVEY_URL'],
            'collectionexercise-service': current_app.config['COLLECTION_EXERCISE_URL'],
            'case-service': current_app.config['CASE_URL'],
            'party-service': current_app.config['PARTY_URL']
        }[service]
        service_url = f'{service}/{endpoint}/{search_value}'
        log.info(f'Making request to {service_url}')
    except KeyError:
        raise RasError(f"service '{service}' not configured", 500)

    response = requests.get(service_url, auth=auth)
    response.raise_for_status()
    return response


def collection_instrument_link(json_message):
    """
    Makes a post request to collection exercise service acknowledging collection instrument load
    :param: json_message
    :type: json
    :return: response
    """

    auth = (current_app.config.get('SECURITY_USER_NAME'), current_app.config.get('SECURITY_USER_PASSWORD'))

    try:
        collection_exercise_url = current_app.config['COLLECTION_EXERCISE_URL']
        url = f'{collection_exercise_url}/collection-instrument/link'
        log.info('Making request to collection exercise to acknowledge instrument load')
    except KeyError:
        raise RasError("collection exercise service not configured", 500)

    response = requests.post(url, json=json_message, auth=auth)
    response.raise_for_status()
    return response
