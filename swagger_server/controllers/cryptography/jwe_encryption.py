import base64


class JWEEncrypter(object):

    @staticmethod
    def _base_64_encode(text):
        # strip the trailing = as they are padding to make the result a multiple of 4
        # the RFC does the same, as do other base64 libraries so this is a safe operation
        return base64.urlsafe_b64encode(text).decode().strip("=").encode()


ALG_HEADER = "alg"
ALG = "dir"
ENC_HEADER = "enc"
ENC = "A256GCM"
KID_HEADER = "kid"
KID = "1,1"
