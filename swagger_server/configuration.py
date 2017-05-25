##############################################################################
#                                                                            #
#   Generic Configuration tool for Micro-Service environment discovery       #
#   Date:    20 May 2017                                                     #
#   Author:  Gareth Bult                                                     #
#   License: MIT                                                             #
#   Copyright (c) 2017 Crown Copyright (Office for National Statistics)      #
#                                                                            #
#   Initial peer review:                                                     #
#                                                                            #
#   Revision    Date    Reason                                               #
#                                                                            #
##############################################################################
from configparser import ConfigParser, ExtendedInterpolation
from yaml import load, dump
from json import loads
from os import getenv
from pathlib import Path
from sqlalchemy import create_engine, event, DDL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy_utils import database_exists, create_database
from .controllers_local.encryption import ONSCryptographer

class ONSEnvironment(object):

    def __init__(self):
        """
        Nothing actually happens at this point, we're just setting up variables
        for future reference. In particular _base and _env are critical to the
        setup of other components.
        """
        self._port = 0
        self._crypto_key = None
        self._ons_cipher = None
        self._config = ConfigParser()
        self._config._interpolation = ExtendedInterpolation()
        self._config.read('config.ini')
        self._env = getenv('ONS_ENV', 'development')
        self._session = scoped_session(sessionmaker())
        self._base = declarative_base()
        #
        #   If we're using postgres, make sure we create the appropriate Schema if it
        #   doesn't already exist.
        #
        schema = self.get('db_schema')
        if schema:
            event.listen(
                self._base.metadata,
                "before_create",
                DDL('CREATE SCHEMA IF NOT EXISTS {}'.format(schema)).execute_if(dialect='postgresql')
            )
        self._engine = create_engine(self.get('db_connection'), convert_unicode=True)

    def activate(self):
        """
        Activate the database, then set up the Cloud Foundry environment if there is one ...
        """
        self._activate_database()
        self._activate_cf()
        self._ons_cipher = ONSCryptographer(self._crypto_key)

    def _activate_database(self):
        """
        Connect to the database (create it if it's missing) and set up tables as per our models.
        If we're in a 'test' environment, drop all the tables first ...
        """
        self._session.remove()
        self._session.configure(bind=self._engine, autoflush=False, autocommit=False, expire_on_commit=False)
        if not database_exists(self._engine.url):
            create_database(self._engine.url)
        if self.if_drop_database:
            self._base.metadata.drop_all(self._engine)
        from .models_local import _models
        self._base.metadata.create_all(self._engine)

    def _activate_cf(self):
        """
        If we're running on Cloud Foundry we need to set the host in the swagger YAML file to be
        the hostname we recover from VCAP application. We also need to set the configuration port for
        use by the listener if we're running locally.
        """
        self._crypto_key = getenv('ONS_CRYPTOKEY', self.get('crypto_key'))
        config = './swagger_server/swagger/swagger.yaml'
        if not Path(config).is_file():
            raise Exception('%% swagger configuration is missing')
        with open(config) as io:
            code = load(io)
        if len(code['host'].split(':')) > 1:
            self._port = code['host'].split(':')[1]

        cf_app_env = getenv('VCAP_APPLICATION')
        if cf_app_env is not None:
            host = loads(cf_app_env)['application_uris'][0]
            code['host'] = host
            if len(host.split(':')) > 1:
                self._port = int(host.split(':')[1])
            with open(config, 'w') as io:
                io.write(dump(code))

        self._port = getenv('PORT', self._port)

    def get(self, key):
        """
        Get a value from config.ini, the actual value recovered is dependent on the
        key, but also on the environment that has been set with ONS_ENV.
        
        :param key: Item to recover from the .ini file 
        :return: Value recovered from the .ini file (or None)
        """
        if self._env not in self._config:
            return None
        if key not in self._config[self._env]:
            return None
        return self._config[self._env][key]

    @property
    def if_drop_database(self):
        drop = self.get('db_drop')
        if not drop:
            return False
        return drop.lower() in ['yes', 'true']

    @property
    def base(self):
        return self._base

    @property
    def session(self):
        return self._session

    @property
    def port(self):
        return self._port

    @property
    def cipher(self):
        return self._ons_cipher


ons_env = ONSEnvironment()
