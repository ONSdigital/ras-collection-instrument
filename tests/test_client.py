import logging

import structlog
from flask_testing import TestCase

from application.models import models
from run import create_app


logger = structlog.wrap_logger(logging.getLogger(__name__))


class TestClient(TestCase):

    @staticmethod
    def create_app():
        return create_app('TestingConfig', init_rabbit=False)

    def tearDown(self):
        models.Base.metadata.drop_all(self.app.db)
        models.Base.metadata.create_all(self.app.db)
        self.app.db.session.commit()
