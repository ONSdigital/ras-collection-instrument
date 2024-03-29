class RasError(Exception):
    status_code = 500

    def __init__(self, errors, status_code=None):
        self.errors = errors if isinstance(errors, list) else [errors]
        self.status_code = status_code or RasPartyError.status_code

    def to_dict(self):
        return {"errors": self.errors}


class GCPBucketException(Exception):
    def __init__(self, error, status_code):
        super().__init__()
        self.error = error
        self.status_code = status_code


class ServiceUnavailableException(RasError):
    pass


class RasDatabaseError(RasError):
    pass


class RasPartyError(RasError):
    pass


class RasNotifyError(RasError):
    pass
