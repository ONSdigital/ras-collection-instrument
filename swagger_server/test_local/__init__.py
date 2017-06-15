from flask_testing import TestCase
import connexion
import logging
from ons_ras_common import ons_env


class BaseTestCase(TestCase):

    def create_app(self):
        ons_env.setup()
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.add_api('swagger.yaml')
        return app.app
