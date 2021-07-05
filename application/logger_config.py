import logging
import os
import sys

from structlog import configure
from structlog.processors import JSONRenderer, TimeStamper, format_exc_info
from structlog.stdlib import add_log_level, filter_by_level


def logger_initial_config(service_name=None, log_level=None, logger_format=None, logger_date_format=None):

    if not logger_date_format:
        logger_date_format = os.getenv("LOGGING_DATE_FORMAT", "%Y-%m-%dT%H:%M%s")
    if not log_level:
        log_level = os.getenv("LOGGING_LEVEL")
    if not logger_format:
        logger_format = "%(message)s"
    try:
        indent = int(os.getenv("JSON_INDENT_LOGGING"))
    except TypeError:
        indent = None
    except ValueError:
        indent = None

    def add_service(logger, method_name, event_dict):  # pylint: disable=unused-argument
        """
        Add the service name to the event dict.
        """
        event_dict["service"] = service_name
        return event_dict

    def add_severity_level(logger, method_name, event_dict):
        """
        Add the log level to the event dict.
        """
        if method_name == "warn":
            # The stdlib has an alias
            method_name = "warning"

        event_dict["severity"] = method_name
        return event_dict

    logging.basicConfig(stream=sys.stdout, level=log_level, format=logger_format)
    configure(
        processors=[
            add_severity_level,
            add_log_level,
            filter_by_level,
            add_service,
            format_exc_info,
            TimeStamper(fmt=logger_date_format, utc=True, key="created_at"),
            JSONRenderer(indent=indent),
        ]
    )
