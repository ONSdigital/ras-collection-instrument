import logging
import structlog
import os
from flask_testing import TestCase
from run import create_app, initialise_db
from retrying import RetryError

logger = structlog.wrap_logger(logging.getLogger(__name__))


class TestClient(TestCase):

    @staticmethod
    def create_app():
        app = create_app()
        try:
            initialise_db(app)
        except RetryError:
            logger.exception('Failed to initialise database')
            exit(1)
        return app

    @staticmethod
    def tearDown():
        os.remove('ras-ci')
