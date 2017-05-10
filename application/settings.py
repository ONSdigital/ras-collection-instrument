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

ONS_OAUTH_PROTOCOL = os.environ.get('ONS_OAUTH_PROTOCOL', 'http://')
ONS_OAUTH_SERVER = os.environ.get('ONS_OAUTH_SERVER', 'localhost:8040')
RAS_COLLECTION_INSTRUMENT_CLIENT_ID = os.environ.get('RAS_COLLECTION_INSTRUMENT_CLIENT_ID', 'ons@ons.gov')
RAS_COLLECTION_INSTRUMENT_CLIENT_SECRET = os.environ.get('RAS_COLLECTION_INSTRUMENT_CLIENT_SECRET', 'password')
ONS_AUTHORIZATION_ENDPOINT = os.environ.get('ONS_AUTHORIZATION_ENDPOINT', '/web/authorize/')
ONS_TOKEN_ENDPOINT = os.environ.get('ONS_TOKEN_ENDPOINT', '/api/v1/tokens/')
ONS_ADMIN_ENDPOINT = os.environ.get('ONS_ADMIN_ENDPOINT', '/api/account/create')

