"""
Module to generate jwt token
"""

from jose import jwt

JWT_ALGORITHM = 'HS256'
JWT_SECRET = 'vrwgLNWEffe45thh545yuby'


def encode(data):
    """
    Function to encode pythn dict data
    """
    return jwt.encode(data, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode(token):
    """
    Function to decode pythn dict data
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
