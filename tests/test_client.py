import logging
import structlog

from flask_testing import TestCase

from application.logger_config import logger_initial_config
from application.models import models
from run import create_app, create_database

logger = structlog.wrap_logger(logging.getLogger(__name__))


class TestClient(TestCase):

    @staticmethod
    def create_app():
        app = create_app('TestingConfig')
        logger_initial_config(service_name='ras-collection-instrument', log_level=app.config['LOGGING_LEVEL'])
        app.db = create_database(app.config['DATABASE_URI'], app.config['DATABASE_SCHEMA'], app.config['DB_POOL_SIZE'],
                                 app.config['DB_MAX_OVERFLOW'], app.config['DB_POOL_RECYCLE'])
        return app

    def tearDown(self):
        models.Base.metadata.drop_all(self.app.db)
        models.Base.metadata.create_all(self.app.db)
        self.app.db.session.commit()
