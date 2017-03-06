import os
basedir = os.path.abspath(os.path.dirname(__file__))

# ENV VARIABLES BELOW, SET THESE ON YOUR TERMINAL
# export APP_SETTINGS=config.Config
# export FLASK_APP=app.py

# Default values
if "APP_SETTINGS" not in os.environ:
    os.environ["APP_SETTINGS"] = "config.Config"


class Config(object):
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'this-really-needs-to-be-changed'
    SQLALCHEMY_DATABASE_URI = "postgresql://ras_collection_instrument:password@localhost:5431/postgres"
    # "postgresql://


class ProductionConfig(Config):
    DEBUG = False


class StagingConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class DevelopmentConfig(Config):
    DEVELOPMENT = True
    DEBUG = True


class TestingConfig(Config):
    TESTING = True


class OAuthConfig(Config):
    """
    This class is used to configure OAuth2 parameters for the microservice.
    This is temporary until an admin config feature
    is added to allow manual config of the microservice
    """
    APP_ID = "399360140422360"  # This is an APP ID registered with the Facebook OAuth2
    APP_SECRET = "8daae4110e491db2c5067e5c89add2dd"  # This is the app secret for a test registered Facebook OAuth2
    DISPLAY_NAME = "NoisyAtom"   # This is a test name registered with Facebook OAuth2
    REDIRECT_ENDPOINT = ["http://104.236.14.123:8002/auth/callback", "http://104.236.14.123:8002/auth/callback.html"]
    AUTHORIZATION_ENDPOINT = "https://www.facebook.com/dialog/oauth"  # Facebook Authorisation endpoint
    TOKEN_ENDPOINT = "https://graph.facebook.com/oauth/access_token"  # Facebook token endpoint


