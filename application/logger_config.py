import logging
import os
import sys

import flask
from flask import g
from structlog import configure
from structlog.processors import JSONRenderer, TimeStamper
from structlog.stdlib import add_log_level, filter_by_level


def logger_initial_config(service_name=None,
                          log_level=None,
                          logger_format=None,
                          logger_date_format=None):

    if not logger_date_format:
        logger_date_format = os.getenv('LOGGING_DATE_FORMAT', "%Y-%m-%dT%H:%M%s")
    if not log_level:
        log_level = os.getenv('LOGGING_LEVEL')
    if not logger_format:
        logger_format = "%(message)s"
    try:
        indent = int(os.getenv('JSON_INDENT_LOGGING'))
    except TypeError:
        indent = None
    except ValueError:
        indent = None

    def add_service(logger, method_name, event_dict):  # pylint: disable=unused-argument
        """
        Add the service name to the event dict.
        """
        event_dict['service'] = service_name
        return event_dict

    def zipkin_ids(logger, method_name, event_dict):
        event_dict['zipkin_trace_id'] = ''
        event_dict['zipkin_span_id'] = ''
        if not flask.has_app_context():
            return event_dict
        if '_zipkin_span' not in g:
            return event_dict
        event_dict['zipkin_span_id'] = g._zipkin_span.zipkin_attrs.span_id
        event_dict['zipkin_trace_id'] = g._zipkin_span.zipkin_attrs.trace_id
        return event_dict

    logging.basicConfig(stream=sys.stdout, level=log_level, format=logger_format)
    configure(processors=[zipkin_ids, add_log_level, filter_by_level, add_service,
                          TimeStamper(fmt=logger_date_format, utc=True, key="created_at"),
                          JSONRenderer(indent=indent)])
