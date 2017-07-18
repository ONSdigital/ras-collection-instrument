class UploadException(Exception):
    """ Generic Ras exception """

    status_code = 400
    message = "Upload failed"

    def __init__(self, message=None, status_code=None):
        Exception.__init__(self)

        if message is not None:
            self.message = message
        if status_code is not None:
            self.status_code = status_code

