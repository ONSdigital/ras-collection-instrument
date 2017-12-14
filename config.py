import os


class Config(object):
    NAME = os.getenv('RAS-COLLECTION-INSTRUMENT')
    VERSION = os.getenv('VERSION', '1.0.2')
    SCHEME = os.getenv('http')
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = os.getenv('PORT', 8002)
    DEBUG = os.getenv('DEBUG', False)
    LOGGING_LEVEL = os.getenv('LOGGING_LEVEL', 'INFO')
    DATABASE_SCHEMA = os.getenv('DATABASE_SCHEMA', 'ras-collection-instrument')
    DATABASE_URI = os.getenv('DATABASE_URI', "sqlite:///:memory:")
    ONS_CRYPTOKEY = os.getenv('CRYPTOKEY')
    SECURITY_USER_NAME = os.getenv('SECURITY_USER_NAME', 'test_user_name')
    SECURITY_USER_PASSWORD = os.getenv('SECURITY_USER_PASSWORD', 'test_user_password')
    RABBITMQ_AMQP = os.getenv('RABBIT_AMQP', 'rabbit_amqp')

    UPLOAD_FILE_XLS = os.getenv('UPLOAD_FILE_XLS', 'xls')
    UPLOAD_FILE_XLSX = os.getenv('UPLOAD_FILE_XLSX', 'xlsx')
    UPLOAD_FILE_EXTENSIONS = (UPLOAD_FILE_XLS, UPLOAD_FILE_XLSX)

    MAX_UPLOAD_FILE_NAME_LENGTH = os.getenv('MAX_UPLOAD_FILE_NAME_LENGTH', 50)

    RAS_COLLECTION_INSTRUMENT_DATABASE_SCHEMA = os.getenv('RAS_COLLECTION_INSTRUMENT_DATABASE_SCHEMA', 'ras_ci')
    RAS_COLLECTION_INSTRUMENT_DATABASE_URI = os.getenv('RAS_COLLECTION_INSTRUMENT_DATABASE_URI', 'sqlite:///ras-ci')

    CASE_SERVICE_PROTOCOL = os.getenv('CASE_SERVICE_PROTOCOL', 'http')
    CASE_SERVICE_HOST = os.getenv('CASE_SERVICE_HOST', 'localhost')
    CASE_SERVICE_PORT = os.getenv('CASE_SERVICE_PORT', 8171)
    CASE_SERVICE = '{}://{}:{}/'.format(CASE_SERVICE_PROTOCOL,
                                        CASE_SERVICE_HOST,
                                        CASE_SERVICE_PORT)

    RM_SURVEY_SERVICE_HOST = os.getenv('RM_SURVEY_SERVICE_HOST', 'localhost')
    RM_SURVEY_SERVICE_PORT = os.getenv('RM_SURVEY_SERVICE_PORT', 8080)
    RM_SURVEY_SERVICE_PROTOCOL = os.getenv('RM_SURVEY_SERVICE_PROTOCOL', 'http')
    RM_SURVEY_SERVICE = '{}://{}:{}/'.format(RM_SURVEY_SERVICE_PROTOCOL,
                                             RM_SURVEY_SERVICE_HOST,
                                             RM_SURVEY_SERVICE_PORT)
