##############################################################################
#                                                                            #
#   Microservices header template                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from flask_basicauth import BasicAuth
from ons_ras_common import ons_env

if __name__ == '__main__':

    def callback(app):
        from swagger_server.controllers.exceptions import UploadException
        from swagger_server.controllers.error_handlers import upload_exception_handler
        app.app.register_error_handler(UploadException, upload_exception_handler)
        app.app.config['BASIC_AUTH_USERNAME'] = ons_env.security_user_name
        app.app.config['BASIC_AUTH_PASSWORD'] = ons_env.security_user_password
        app.app.config['BASIC_AUTH_REALM'] = ons_env.security_realm
        # FIXME: this is a terrible bodge to make basic_auth available, ultimately ras-common needs to be rewritten
        ons_env.basic_auth = BasicAuth(app.app)

    ons_env.activate(callback)
