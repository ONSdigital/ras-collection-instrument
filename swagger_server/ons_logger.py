import logging
import datetime
import sys
import structlog

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

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=LEVELS.get(log_level.lower(), logging.INFO)
    )

    processors = [
            structlog.stdlib.filter_by_level,
            add_service_name,
            add_timestamp,
            structlog.stdlib.add_log_level,
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(sort_keys=True)
    ]
    structlog.configure(
        processors=processors,
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True
    )
    return logger


def add_service_name(logger, method_name, event_dict):  # pylint: disable=unused-argument
    """
    Add the service name to the event dict.
    """
    event_dict['service'] = 'ras-collection-instrument'
    return event_dict


def add_timestamp(logger, method_name, event_dict):
    """
    Add formatted timestamp to event dict.
    """
    event_dict['created'] = datetime.datetime.utcnow().isoformat()[:-3]  # Milliseconds to 3 d.p.
    return event_dict
