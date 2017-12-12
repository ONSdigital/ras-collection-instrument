from flask_testing import TestCase
from ras_common_utils.ras_config import ras_config
from ras_common_utils.ras_logger.ras_logger import configure_logger
from run import create_app, initialise_db
import os


class TestClient(TestCase):

    @staticmethod
    def create_app():
        config_path = 'config/config.yaml'
        config = ras_config.from_yaml_file(config_path)
        app = create_app(config)
        configure_logger(app.config)
        initialise_db(app)
        return app

    @staticmethod
    def tearDown():
        os.remove('ras-ci')
