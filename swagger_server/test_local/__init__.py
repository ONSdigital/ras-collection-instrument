from flask_testing import TestCase
import connexion
import logging
from ons_ras_common import ons_env
from swagger_server.controllers_local.exceptions import SessionScopeException
from swagger_server.controllers_local.error_handlers import session_scope_handler


class BaseTestCase(TestCase):

    def create_app(self):
        ons_env.setup()
        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.add_api('swagger.yaml')
        app.app.register_error_handler(SessionScopeException, session_scope_handler)
        return app.app
