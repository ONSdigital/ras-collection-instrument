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
        log.error("Case not found for {}".format(case_id))
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
        log.info('Collection Exercise not found for {}'.format(collection_exercise_id))
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
        log.debug('Survey service data not found')

    return survey_ref


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
            'survey-service': current_app.config['RM_SURVEY_SERVICE'],
            'collectionexercise-service': current_app.config['COLLECTION_EXERCISE_SERVICE'],
            'case-service': current_app.config['CASE_SERVICE'],
        }[service]
        service_url = f'{service}/{endpoint}/{search_value}'
        log.info(f'Making request to {service_url}')
    except KeyError:
        raise RasError(f"service '{service}' not configured", 500)

    response = requests.get(service_url, auth=auth)
    response.raise_for_status()
    return response
