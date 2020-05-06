import os
from distutils.util import strtobool

from application.cloud.cloudfoundry import ONSCloudFoundry

cf = ONSCloudFoundry()


class Config(object):
    VERSION = '1.4.1'
    SCHEME = os.getenv('http')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = os.getenv('PORT', 8002)
    DEBUG = os.getenv('DEBUG', False)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
    JSON_SECRET_KEYS = os.getenv('JSON_SECRET_KEYS')
    ONS_CRYPTOKEY = os.getenv('ONS_CRYPTOKEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    MAX_UPLOAD_FILE_NAME_LENGTH = os.getenv('MAX_UPLOAD_FILE_NAME_LENGTH', 50)
    COLLECTION_EXERCISE_SCHEMA = os.getenv('COLLECTION_EXERCISE_SCHEMA',
                                           'application/schemas/collection_instrument_schema.json')

    RABBITMQ_AMQP_COLLECTION_INSTRUMENT = cf.rm_queue_uri
    RABBITMQ_AMQP_SURVEY_RESPONSE = cf.sdx_queue_uri
    DATABASE_URI = cf.db_uri
    DB_POOL_SIZE = int(os.getenv('DB_POOL_SIZE', 5))
    DB_MAX_OVERFLOW = int(os.getenv('DB_MAX_OVERFLOW', 10))
    DB_POOL_RECYCLE = int(os.getenv('DB_POOL_RECYCLE', -1))

    if cf.detected:
        DATABASE_SCHEMA = 'ras_ci'
    else:
        DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'ras_ci')

    UPLOAD_FILE_EXTENSIONS = 'xls,xlsx'


    # dependencies

    CASE_SERVICE_PROTOCOL = os.getenv('CASE_SERVICE_PROTOCOL', 'http')
    CASE_SERVICE_HOST = os.getenv('CASE_SERVICE_HOST', 'localhost')
    CASE_SERVICE_PORT = os.getenv('CASE_SERVICE_PORT', 8171)
    CASE_SERVICE = '{}://{}:{}'.format(CASE_SERVICE_PROTOCOL,
                                       CASE_SERVICE_HOST,
                                       CASE_SERVICE_PORT)

    COLLECTION_EXERCISE_PROTOCOL = os.getenv('COLLECTION_EXERCISE_PROTOCOL', 'http')
    COLLECTION_EXERCISE_HOST = os.getenv('COLLECTION_EXERCISE_HOST', 'localhost')
    COLLECTION_EXERCISE_PORT = os.getenv('COLLECTION_EXERCISE_PORT', 8145)
    COLLECTION_EXERCISE_SERVICE = '{}://{}:{}'.format(COLLECTION_EXERCISE_PROTOCOL,
                                                      COLLECTION_EXERCISE_HOST,
                                                      COLLECTION_EXERCISE_PORT)

    SURVEY_SERVICE_PROTOCOL = os.getenv('SURVEY_SERVICE_PROTOCOL', 'http')
    SURVEY_SERVICE_HOST = os.getenv('SURVEY_SERVICE_HOST', 'localhost')
    SURVEY_SERVICE_PORT = os.getenv('SURVEY_SERVICE_PORT', 8080)
    SURVEY_SERVICE = '{}://{}:{}'.format(SURVEY_SERVICE_PROTOCOL,
                                         SURVEY_SERVICE_HOST,
                                         SURVEY_SERVICE_PORT)

    PARTY_SERVICE_PROTOCOL = os.getenv('PARTY_SERVICE_PROTOCOL', 'http')
    PARTY_SERVICE_HOST = os.getenv('PARTY_SERVICE_HOST', 'localhost')
    PARTY_SERVICE_PORT = os.getenv('PARTY_SERVICE_PORT', 8081)
    PARTY_SERVICE = f'{PARTY_SERVICE_PROTOCOL}://{PARTY_SERVICE_HOST}:{PARTY_SERVICE_PORT}'


class DevelopmentConfig(Config):
    DEBUG = os.getenv('DEBUG', True)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')


class TestingConfig(Config):
    DEBUG = True
    LOGGING_LEVEL = 'ERROR'
    SECURITY_USER_NAME = 'admin'
    SECURITY_USER_PASSWORD = 'secret'
    DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'postgresql://postgres:postgres@localhost:6432/postgres')
    RABBITMQ_AMQP_COLLECTION_INSTRUMENT = os.getenv('RABBITMQ_AMQP_COLLECTION_INSTRUMENT',
                                                    'amqp://guest:guest@localhost:5672')
    RABBITMQ_AMQP_SURVEY_RESPONSE = os.getenv('RABBITMQ_AMQP_SURVEY_RESPONSE', 'amqp://guest:guest@localhost:5672')
    DATABASE_SCHEMA = 'ras_ci'
    ONS_CRYPTOKEY = 'somethingsecure'
    JSON_SECRET_KEYS = open("./tests/files/keys.json").read()
