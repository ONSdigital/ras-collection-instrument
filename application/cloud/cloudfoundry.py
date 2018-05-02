import cfenv


class ONSCloudFoundry(object):

    def __init__(self):
        self._cf_env = cfenv.AppEnv()

    @property
    def detected(self):
        return self._cf_env.app

    @property
    def db(self):
        return self._cf_env.get_service(name='ras-ci-db')

    @property
    def queue(self):
        try:
            return self._cf_env.get_service(name='ras-rabbitmq')
        except StopIteration:
            return None
