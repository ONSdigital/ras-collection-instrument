import logging
import structlog
from application.logger_config import logger_initial_config

from flask_testing import TestCase
from run import create_app, initialise_db

logger = structlog.wrap_logger(logging.getLogger(__name__))


class TestClient(TestCase):

    @staticmethod
    def create_app():
        app = create_app()
        logger_initial_config(service_name='ras-collection-instrument', log_level=app.config['LOGGING_LEVEL'])
        app.config.from_object('config.TestingConfig')
        initialise_db(app)
        return app
