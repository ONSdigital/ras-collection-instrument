import os

''' This file is the main configuration for the Collection Instrument Service.
    It contains a full default configuration
    All configuration may be overridden by setting the appropriate environment variable name. '''

DEBUG = False
TESTING = False
CSRF_ENABLED = True
SECRET_KEY = 'this-really-needs-to-be-changed'
dbname = "ras_collection_instrument"
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', "postgresql://" + dbname + ":password@localhost:5431/postgres")


#OAuthConfig
    # """
    # This class is used to configure OAuth2 parameters for the microservice.
    # This is temporary until an admin config partyser
    # is added to allow manual config of the microservice
    # """
    # APP_ID = "399360140422360"  # This is an APP ID registered with the Facebook OAuth2
    #
    # # App secret for a test registered Facebook OAuth2
    # APP_SECRET = "8daae4110e491db2c5067e5c89add2dd"
    #
    # DISPLAY_NAME = "NoisyAtom"  # This is a test name registered with Facebook OAuth2
    # REDIRECT_ENDPOINT = ["http://104.236.14.123:8002/auth/callback",
    #                      "http://104.236.14.123:8002/auth/callback.html"]
    #
    # AUTHORIZATION_ENDPOINT = "https://www.facebook.com/dialog/oauth"  # Facebook Auth endpoint
    # TOKEN_ENDPOINT = "https://graph.facebook.com/oauth/access_token"  # Facebook token endpoint
    #
    # ONS_OAUTH_PROTOCOL = "http://"
    # ONS_OAUTH_SERVER = "localhost:8000"
    # RAS_FRONTSTAGE_CLIENT_ID = "onc@onc.gov"
    # RAS_FRONTSTAGE_CLIENT_SECRET = "password"
    # ONS_AUTHORIZATION_ENDPOINT = "/web/authorize/"
    # ONS_TOKEN_ENDPOINT = "/api/v1/tokens/"
    # ONS_ADMIN_ENDPOINT = '/api/account/create'
