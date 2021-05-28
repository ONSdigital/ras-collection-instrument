import gnupg
import json


class GNUEncrypter:

    def __init__(self, public_key, passphrase=None, always_trust=True):
        self.gpg = gnupg.GPG()
        self.gpg.import_keys(public_key.encode('utf-8'))

    def encrypt(self, payload, recipient):
        """
        Encrypts the payload using the recipient values

        :param payload: the value to encrypt
        :param recipient: who is it for
        :return: string of encrypted data
        """
        payload = 'hello world'
        enc_data = self.gpg.encrypt(json.dumps(payload).encode('utf-8'), recipient, always_trust=True)
        if not enc_data.ok:
            print('ok: ', enc_data.ok)
            print('status: ', enc_data.status)
            print('stderr: ', enc_data.stderr)
            print('unencrypted_string: ', payload)
            print('encrypted_string: ', enc_data)
            print('payload:', payload)
            print('recipient:', recipient)
            raise ValueError('Failed to GNU encrypt bag: {}.'
                             '  Have you installed a required public key?'.format(enc_data.status))
        return str(enc_data)
