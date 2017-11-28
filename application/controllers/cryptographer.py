from base64 import b64encode
from Crypto import Random
from Crypto.Cipher import AES
from flask import current_app
from hashlib import sha256


class Cryptographer:

    def __init__(self):
        key = current_app.config.get('ONS_CRYPTOKEY')
        self._key = sha256(key.encode('utf-8')).digest()

    @staticmethod
    def pad(data):
        """
        Pad the data out to the selected block size.

        :param data: The data were trying to encrypt
        :return: The data padded out to our given block size
        """
        vector = AES.block_size - len(data) % AES.block_size
        return data + ((bytes([vector])) * vector)

    def encrypt(self, raw_text):
        """
        Encrypt the supplied text

        :param raw_text: The data to encrypt, must be a string of type byte
        :return: The encrypted text
        """
        raw_text = self.pad(raw_text)
        init_vector = Random.new().read(AES.block_size)
        ons_cipher = AES.new(self._key, AES.MODE_CBC, init_vector)
        return b64encode(init_vector + ons_cipher.encrypt(raw_text))
