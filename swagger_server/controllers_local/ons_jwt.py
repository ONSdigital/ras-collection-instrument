##############################################################################
#                                                                            #
#   ONS Digital JWT token handling                                           #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
##############################################################################
from ..configuration import ons_env
from jose import jwt, JWTError
from datetime import datetime
from sys import _getframe
from functools import wraps
from logging import WARN, INFO, ERROR, DEBUG


def validate_jwt(scope, request):
    """
    Validate the incoming JWT token, don't allow access to the endpoint unless we pass this test
    :param scope: A list of scope identifiers used to protect the endpoint
    :param request: The incoming request object
    :return: Exit variables from the protected function
    """
    def authorization_required_decorator(original_function):
        @wraps(original_function)
        def authorization_required_wrapper(*args, **kwargs):
            if not ons_env.is_secure:
                return original_function(*args, **kwargs)
            if my_token.validate(scope, request.headers.get('authorization', '')):
                return original_function(*args, **kwargs)
            return "Access forbidden", 403
        return authorization_required_wrapper
    return authorization_required_decorator


class ONSToken(object):

    def __init__(self):
        self.algorithm = ons_env.get('jwt_algorithm')
        self.secret = ons_env.get('jwt_secret')
        self.token = None

    def report(self, lvl, msg):
        """
        Report an issue to the external logging infrastructure
        :param lvl: The log level we're outputting to
        :param msg: The message we want to log
        :return:
        """
        line = _getframe(1).f_lineno
        name = _getframe(1).f_code.co_name
        ons_env.logger.log(lvl, "{}: #{} - {}".format(name, line, msg))
        return False

    def encode(self, data):
        """
        Function to encode python dict data
        :param: The data to convert into a token
        :return: A JWT token
        """
        return jwt.encode(data, self.secret, algorithm=self.algorithm)

    def decode(self, token):
        """
        Function to decode python dict data
        :param: token - the token to decode
        :return: the decrypted token in dict format
        """
        return jwt.decode(token, self.secret, algorithms=[self.algorithm])

    def validate(self, scope, jwt_token):
        """
        This function checks a jwt token for a required scope type.
        :param scope: The scopes to test against
        :param jwt_token: The incoming request object
        :return: Token is value, True or False
        """
        self.report(INFO, 'validating token "{}" for scope "{}"'.format(jwt_token, scope))
        try:
            token = self.decode(jwt_token)
        except JWTError:
            return self.report(ERROR, 'unable to decode token "{}"'.format(jwt_token))
        #
        #   Make sure the token hasn't expired on us ...
        #
        now = datetime.now().timestamp()
        if now >= token.get('expires_at', now):
            return self.report(WARN, 'token has expired "{}"'.format(token))
        #
        #   See if there is an intersection between the scopes required for this endpoint
        #   end and the scopes available in the token.
        #
        if not set(scope).intersection(token.get('scope', [])):
            return self.report(WARN, 'unable to validate scope for "{}"'.format(token))
        self.report(INFO, 'validated scope for "{}"'.format(token))
        return True

my_token = ONSToken()
