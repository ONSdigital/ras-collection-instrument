from flask_testing import TestCase
from ..encoder import JSONEncoder
import connexion
import logging
from ..configuration import ons_env

class BaseTestCase(TestCase):

    def create_app(self):
        ons_env.activate()
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.app.json_encoder = JSONEncoder
        app.add_api('swagger.yaml')
        return app.app
