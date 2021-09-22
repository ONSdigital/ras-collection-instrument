import os


class Config(object):
    VERSION = "1.4.1"
    SCHEME = os.getenv("http")
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = os.getenv("PORT", 8002)
    DEBUG = os.getenv("DEBUG", False)
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")
    JSON_SECRET_KEYS = os.getenv("JSON_SECRET_KEYS")
    ONS_CRYPTOKEY = os.getenv("ONS_CRYPTOKEY")
    ONS_GNU_PUBLIC_CRYPTOKEY = os.getenv("ONS_GNU_PUBLIC_CRYPTOKEY")
    ONS_GNU_RECIPIENT = os.getenv("ONS_GNU_RECIPIENT")
    ONS_GNU_FINGERPRINT = os.getenv("ONS_GNU_FINGERPRINT")
    SECURITY_USER_NAME = os.getenv("SECURITY_USER_NAME", "admin")
    SECURITY_USER_PASSWORD = os.getenv("SECURITY_USER_PASSWORD", "secret")
    MAX_UPLOAD_FILE_NAME_LENGTH = os.getenv("MAX_UPLOAD_FILE_NAME_LENGTH", 50)
    DATABASE_URI = os.getenv("DATABASE_URI", "postgresql://postgres:postgres@localhost:6432/postgres")
    DATABASE_SCHEMA = os.getenv("DATABASE_SCHEMA", "ras_ci")

    SEFT_BUCKET_NAME = os.getenv("SEFT_BUCKET_NAME", "test-bucket")
    # Prefix only used for dev environments to file in folders within the bucket
    SEFT_BUCKET_FILE_PREFIX = os.getenv("SEFT_BUCKET_FILE_PREFIX")
    SEFT_PUBSUB_TOPIC = os.getenv("SEFT_PUBSUB_TOPIC", "ras-rm-notify-test")
    SEFT_CI_BUCKET_NAME = os.getenv("SEFT_CI_BUCKET_NAME")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    SEFT_CI_BUCKET_FILE_PREFIX = os.getenv("SEFT_CI_BUCKET_FILE_PREFIX")
    SEFT_CI_DATABASE_TABLE_DEPRECATED = os.getenv("SEFT_CI_DATABASE_TABLE_DEPRECATED")

    UPLOAD_FILE_EXTENSIONS = "xls,xlsx"

    # Dependencies
    CASE_URL = os.getenv("CASE_URL", "http://localhost:8171")
    COLLECTION_EXERCISE_URL = os.getenv("COLLECTION_EXERCISE_URL", "http://localhost:8145")
    PARTY_URL = os.getenv("PARTY_URL", "http://localhost:8081")
    SURVEY_URL = os.getenv("SURVEY_URL", "http://localhost:8080")


class DevelopmentConfig(Config):
    DEBUG = os.getenv("DEBUG", True)
    LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "DEBUG")


class TestingConfig(Config):
    project_root = os.path.dirname(__file__)
    JSON_SECRET_KEYS = open(f"{project_root}/tests/files/keys.json").read()

    DEBUG = True
    LOGGING_LEVEL = "ERROR"
    SECURITY_USER_NAME = "admin"
    SECURITY_USER_PASSWORD = "secret"
    DATABASE_URI = os.getenv("TEST_DATABASE_URI", "postgresql://postgres:postgres@localhost:6432/postgres")
    DATABASE_SCHEMA = "ras_ci"
    ONS_CRYPTOKEY = "somethingsecure"
    SEFT_CI_BUCKET_NAME = "TEST_BUCKET"
    GOOGLE_CLOUD_PROJECT = "TEST_PROJECT"
    SEFT_CI_BUCKET_FILE_PREFIX = ""
    SEFT_CI_DATABASE_TABLE_DEPRECATED = False
