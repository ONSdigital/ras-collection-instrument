import unittest
from datetime import datetime, timedelta
from swagger_server.controllers_local.ons_jwt import ONSToken


class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.ons_token = ONSToken()
        self.now = datetime.now()

    def test_validate_good_token(self):
        """
        Generate a valid token and make sure it passes validation
        """
        jwt = {
            'expires_at': (self.now + timedelta(seconds=60)).timestamp(),
            'scope': ['ci:read', 'ci:write']
        }
        token = self.ons_token.encode(jwt)
        self.assertTrue(self.ons_token.validate(['ci:read'], token))

    def test_validate_expired_token(self):
        """
        Generate an  invalid token and make sure it fails validation
        """
        jwt = {
            'expires_at': (self.now - timedelta(seconds=60)).timestamp(),
            'scope': ['ci:read', 'ci:write']
        }
        token = self.ons_token.encode(jwt)
        self.assertFalse(self.ons_token.validate(['ci:read'], token))

    def test_validate_no_token(self):
        """
        Generate an empty token and make sure it fails validation
        """
        jwt = {}
        token = self.ons_token.encode(jwt)
        self.assertFalse(self.ons_token.validate(['ci:read'], token))

    def test_invalid_scope(self):
        """
        Generate a token with an invalid scope and make sure it fails
        """
        jwt = {
            'expires_at': (self.now + timedelta(seconds=60)).timestamp(),
            'scope': ['cx:read', 'cx:write']
        }
        token = self.ons_token.encode(jwt)
        self.assertFalse(self.ons_token.validate(['ci:read'], token))

    def test_invalid_token(self):
        """
        Try to decode something that really isn't a valid token
        """
        self.assertFalse(self.ons_token.validate(['ci:read'], 'not a token'))
