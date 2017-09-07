from flask_httpauth import HTTPBasicAuth
from ons_ras_common import ons_env

auth = HTTPBasicAuth()


@auth.get_password
def get_pw(username):
    config_username = ons_env.security_user_name
    config_password = ons_env.security_user_password
    if username == config_username:
        return config_password
