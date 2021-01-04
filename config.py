import os


class Config(object):
    VERSION = '1.4.1'
    SCHEME = os.getenv('http')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = os.getenv('PORT', 8002)
    DEBUG = os.getenv('DEBUG', False)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'DEBUG')
    JSON_SECRET_KEYS = os.getenv('JSON_SECRET_KEYS')
    ONS_CRYPTOKEY = os.getenv('ONS_CRYPTOKEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'admin')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'secret')
    MAX_UPLOAD_FILE_NAME_LENGTH = os.getenv('MAX_UPLOAD_FILE_NAME_LENGTH', 50)
    COLLECTION_EXERCISE_SCHEMA = os.getenv('COLLECTION_EXERCISE_SCHEMA',
                                           'application/schemas/collection_instrument_schema.json')

    RABBITMQ_AMQP_COLLECTION_INSTRUMENT = os.getenv('RABBITMQ_AMQP_COLLECTION_INSTRUMENT')
    RABBITMQ_AMQP_SURVEY_RESPONSE = os.getenv('RABBITMQ_AMQP_SURVEY_RESPONSE')
    DATABASE_URI = os.getenv('DATABASE_URI', 'postgresql://postgres:postgres@localhost:6432/postgres')
    DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'ras_ci')

    UPLOAD_FILE_EXTENSIONS = 'xls,xlsx'

    # Dependencies
    CASE_URL = os.getenv('CASE_URL', 'http://localhost:8171')
    COLLECTION_EXERCISE_URL = os.getenv('COLLECTION_EXERCISE_URL', 'http://localhost:8145')
    PARTY_URL = os.getenv('PARTY_URL', 'http://localhost:8081')
    SURVEY_URL = os.getenv('SURVEY_URL', 'http://localhost:8080')


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
