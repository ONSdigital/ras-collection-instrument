"""
Util module
"""

from jwt import decode


def get_jwt_from_header(auth_header_value):
    """
    returns jwt token out of the auth header
    """
    jwt_dict = decode(auth_header_value)
    return jwt_dict
