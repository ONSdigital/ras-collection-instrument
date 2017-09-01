import base64

from flask_testing import TestCase
import connexion
import logging
from ons_ras_common import ons_env


class BaseTestCase(TestCase):

    def create_app(self):
        ons_env.setup_ini()
        ons_env.logger.activate()
        ons_env.db.activate()
        ons_env._jwt.activate()
        ons_env._cryptography.activate()

        logging.getLogger('connexion.operation').setLevel('ERROR')
        app = connexion.App(__name__, specification_dir='../swagger/')
        app.add_api('swagger.yaml')
        return app.app

    @property
    def auth_headers(self):
        auth = "{}:{}".format(ons_env.security_user_name, ons_env.security_user_password).encode('utf-8')
        return {
            'Authorization': 'Basic %s' % base64.b64encode(bytes(auth)).decode("ascii")
        }
