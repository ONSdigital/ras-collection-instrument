import logging

import sys

LEVELS = {'debug': logging.DEBUG,
          'info': logging.INFO,
          'warning': logging.WARNING,
          'error': logging.ERROR,
          'critical': logging.CRITICAL}


def create(config):
    """
    Creates a logger configured according to RAS logging conventions.
    
    :param config: A configuration object, e.g. instance of ONSEnvironment
    :return: 
    """
    name = config.get('service_name', 'RAS service')
    log_level = config.get('log_level', 'WARNING')
    logger = logging.getLogger(name)

    stdout_handler = logging.StreamHandler(sys.stdout)
    logger.addHandler(stdout_handler)
    logger.setLevel(LEVELS.get(log_level.lower(), logging.INFO))
    return logger
