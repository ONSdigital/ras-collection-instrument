from flask import current_app
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()


@auth.get_password
def get_pw(username):
    """
    Returns basic auth password if the username matches the value in app

    :param username: basic auth username
    :return: basic auth password
    """
    config_username = current_app.config["SECURITY_USER_NAME"]
    config_password = current_app.config["SECURITY_USER_PASSWORD"]
    if username == config_username:
        return config_password
