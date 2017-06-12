import unittest
from swagger_server.controllers_local.encryption import ONSCryptographer

class TestStringMethods(unittest.TestCase):

    def setUp(self):
        self.ons_cipher = ONSCryptographer('ONS_SECRET_KEY')

    def test_01_string(self):
        text = b'This is a short string'
        encrypted = self.ons_cipher.encrypt(text)
        decrypted = self.ons_cipher.decrypt(encrypted)
        self.assertEqual(text, decrypted)

    def test_02_string_longer(self):
        text = b'This is a short stringThis is a short stringThis is a short stringThis is a short string'
        encrypted = self.ons_cipher.encrypt(text)
        decrypted = self.ons_cipher.decrypt(encrypted)
        self.assertEqual(text, decrypted)

    def test_03_string_none(self):
        text = b''
        encrypted = self.ons_cipher.encrypt(text)
        decrypted = self.ons_cipher.decrypt(encrypted)
        self.assertEqual(text, decrypted)
