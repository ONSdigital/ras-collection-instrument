import json
import os
from sdc.crypto.key_store import validate_required_keys
from sdc.crypto.key_store import KeyStore
from sdc.crypto.encrypter import encrypt
from swagger_server.controllers.helper import to_str
from swagger_server.controllers.cryptography.keys import TEST_KEYS_YML


KEY_PURPOSE = "inbound"


class Encrypter:

    def __init__(self):
        json_string = os.getenv('CI_SECRETS', TEST_KEYS_YML)

        keys = json.loads(json_string)
        validate_required_keys(keys, KEY_PURPOSE)
        self.keystore = KeyStore(keys)

    def encrypt(self, payload):
        encrypted_data = encrypt(payload, key_store=self.keystore, key_purpose=KEY_PURPOSE)
        return to_str(encrypted_data)
