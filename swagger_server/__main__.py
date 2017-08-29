##############################################################################
#                                                                            #
#   Microservices header template                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ons_ras_common import ons_env

if __name__ == '__main__':

    def callback(app):
        from swagger_server.controllers.exceptions import UploadException
        from swagger_server.controllers.error_handlers import upload_exception_handler
        app.app.register_error_handler(UploadException, upload_exception_handler)

    ons_env.activate(callback)
