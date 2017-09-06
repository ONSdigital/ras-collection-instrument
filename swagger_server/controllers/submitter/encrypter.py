import json
import logging
import os
from sdc.crypto.key_store import validate_required_keys
from sdc.crypto.key_store import KeyStore
from sdc.crypto.encrypter import encrypt
from swagger_server.controllers.helper import to_str
from swagger_server.controllers.cryptography.keys import TEST_KEYS_YML

KEY_PURPOSE = "inbound"


logger = logging.getLogger(__name__)


class Encrypter:

    def __init__(self):
        logger.info("Loading keys from environment")
        json_string = os.getenv('CI_SECRETS', TEST_KEYS_YML)
        keys = json.loads(json_string)
        logger.info("Loaded keys from environment")

        validate_required_keys(keys, KEY_PURPOSE)

        self.keystore = KeyStore(keys)

    def encrypt(self, payload):
        logger.debug("About to encrypted data")
        encrypted_data = encrypt(payload, key_store=self.keystore, key_purpose=KEY_PURPOSE)
        logger.debug("Encrypted")
        return to_str(encrypted_data)
