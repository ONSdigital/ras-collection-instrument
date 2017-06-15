##############################################################################
#                                                                            #
#   Microservices header template                                            #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ons_ras_common import ons_env

if __name__ == '__main__':
    #from swagger_server.controllers_local.exceptions import SessionScopeException
    #from swagger_server.controllers_local.error_handlers import session_scope_handler
    #app.app.register_error_handler(SessionScopeException, session_scope_handler)

    ons_env.activate()
