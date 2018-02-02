import os

from application.cloud.cloudfoundry import ONSCloudFoundry


cf = ONSCloudFoundry()


class Config(object):
    NAME = os.getenv('RAS-COLLECTION-INSTRUMENT', 'ras-collection-instrument')
    VERSION = os.getenv('VERSION', '1.0.4')
    SCHEME = os.getenv('http')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = os.getenv('PORT', 8002)
    DEBUG = os.getenv('DEBUG', False)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
    ONS_CRYPTOKEY = os.getenv('ONS_CRYPTOKEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    RABBITMQ_AMQP = os.getenv('RABBITMQ_AMQP', 'rabbit_amqp')
    MAX_UPLOAD_FILE_NAME_LENGTH = os.getenv('MAX_UPLOAD_FILE_NAME_LENGTH', 50)
    COLLECTION_EXERCISE_SCHEMA = os.getenv('COLLECTION_EXERCISE_SCHEMA',
                                           'application/schemas/collection_instrument_schema.json')

    if cf.detected:
        DATABASE_SCHEMA = 'ras_ci'
        DATABASE_URI = cf.db.credentials['uri']
    else:
        DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'ras_ci')
        DATABASE_URI = os.getenv('DATABASE_URI', 'postgres://postgres:postgres@localhost:6432/postgres')

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

    RM_SURVEY_SERVICE_PROTOCOL = os.getenv('RM_SURVEY_SERVICE_PROTOCOL', 'http')
    RM_SURVEY_SERVICE_HOST = os.getenv('RM_SURVEY_SERVICE_HOST', 'localhost')
    RM_SURVEY_SERVICE_PORT = os.getenv('RM_SURVEY_SERVICE_PORT', 8080)
    RM_SURVEY_SERVICE = '{}://{}:{}'.format(RM_SURVEY_SERVICE_PROTOCOL,
                                            RM_SURVEY_SERVICE_HOST,
                                            RM_SURVEY_SERVICE_PORT)


class DevelopmentConfig(Config):
    DEBUG = os.getenv('DEBUG', True)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')


class TestingConfig(Config):
    DEBUG = True
    LOGGING_LEVEL = 'ERROR'
    SECURITY_USER_NAME = 'admin'
    SECURITY_USER_PASSWORD = 'secret'
    DATABASE_URI = os.getenv('TEST_DATABASE_URI', 'postgres://postgres:postgres@localhost:6432/postgres')
    DATABASE_SCHEMA = 'ras_ci'
    ONS_CRYPTOKEY = 'somethingsecure'
