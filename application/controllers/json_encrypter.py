import json

from sdc.crypto.encrypter import encrypt
from sdc.crypto.key_store import KeyStore
from sdc.crypto.key_store import validate_required_keys

from application.controllers.helper import to_str

KEY_PURPOSE = "inbound"


class Encrypter:
    def __init__(self, json_secret_keys):
        keys = json.loads(json_secret_keys)
        validate_required_keys(keys, KEY_PURPOSE)
        self.keystore = KeyStore(keys)

    def encrypt(self, payload):
        """
        Encrypts the payload using the keystore values

        :param payload: the value to encrypt
        :return: string of encrypted data
        """
        encrypted_data = encrypt(payload, key_store=self.keystore, key_purpose=KEY_PURPOSE)
        return to_str(encrypted_data)
