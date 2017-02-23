import os
basedir = os.path.abspath(os.path.dirname(__file__))

#ENV VARIABLES BELOW, SET THESE ON YOUR TERMINAL
#export APP_SETTINGS=config.Config
#export FLASK_APP=app.py



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


