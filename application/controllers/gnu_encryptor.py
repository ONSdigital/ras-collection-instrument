import gnupg
import json
from pprint import pprint


class GNUEncrypter:

    def __init__(self, public_key, passphrase=None, always_trust=True):
        self.gpg = gnupg.GPG()
        tmp = self.gpg.import_keys(public_key.encode('utf-8'))
        pprint(tmp)

    def encrypt(self, payload, recipient):
        """
        Encrypts the payload using the recipient values

        :param payload: the value to encrypt
        :param recipient: who is it for
        :return: string of encrypted data
        """
        enc_data = self.gpg.encrypt(json.dumps(payload).encode('utf-8'), recipient, always_trust=True)
        if not enc_data.ok:
            raise ValueError('Failed to GNU encrypt bag: {}.'
                             '  Have you installed a required public key?'.format(enc_data.status))
        return str(enc_data)

    def decrypt(self, payload, passphrase):
        """
        Decrypt the payload using the passphase values

        :param payload: the value to decrypt
        :param recipient: who is it for
        :return: string of decrypted data
        """

        decrypted_data = self.gpg.decrypt(payload, passphrase=None)
        if not decrypted_data.ok:
            raise ValueError('Failed to GNU encrypt bag: {}.'
                             '  Have you installed a required public key?'.format(decrypted_data.status))
        return str(decrypted_data)
