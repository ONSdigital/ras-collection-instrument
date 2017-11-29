import requests

from flask import current_app
from ras_common_utils.ras_error.ras_error import RasError
from structlog import get_logger

log = get_logger()


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
        service = current_app.config.dependency[service]
        service_url = '{}://{}:{}/{}/{}'.format(service['scheme'], service['host'],
                                                service['port'], endpoint, search_value)
        log.info('Making request to {}'.format(service_url))
    except KeyError:
        raise RasError('service not configured', 500)

    response = requests.get(service_url, auth=auth)
    response.raise_for_status()
    return response
