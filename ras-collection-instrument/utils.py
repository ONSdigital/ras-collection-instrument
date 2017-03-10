from flask import request

authheader = request.headers.get('authorization')

from jwt import decode

def get_jwt_from_header(auth_header_value):
	jwt_dict = decode(auth_header)
	return jwt_dict


"""
data_dict_for_jwt_token = {"user_id": "c3c0c2cd-bd52-428f-8841-540b1b7dd619",
                           "user_scopes": ['foo', 'bar', 'qux']
                           }
"""
