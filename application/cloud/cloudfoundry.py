import os

import cfenv


class ONSCloudFoundry(object):

    def __init__(self):
        self._cf_env = cfenv.AppEnv()

    @property
    def detected(self):
        return self._cf_env.app

    @property
    def db_uri(self):
        if self._cf_env.get_service(name='ras-ci-db'):
            return self._cf_env.get_service(name='ras-ci-db').credentials['uri']
        else:
            return os.getenv('DATABASE_URI', 'postgresql://postgres:postgres@localhost:6432/postgres')

    @property
    def rm_queue_uri(self):
        if self._cf_env.get_service(name='rm-rabbitmq'):
            return self._cf_env.get_service(name='rm-rabbitmq').credentials['uri']
        else:
            return os.getenv('RABBITMQ_AMQP_COLLECTION_INSTRUMENT', 'rabbit_amqp')

    @property
    def sdx_queue_uri(self):
        if self._cf_env.get_service(name='sdx-rabbitmq'):
            return self._cf_env.get_service(name='sdx-rabbitmq').credentials['uri']
        else:
            return os.getenv('RABBITMQ_AMQP_SURVEY_RESPONSE', 'rabbit_amqp')
