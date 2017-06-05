import argparse
from configparser import ConfigParser, ExtendedInterpolation
from sqlalchemy import create_engine
import sqlalchemy_utils as util
from swagger_server import ons_logger


def drop(config, engine, logger):
    db_connection = config.get('db_connection')
    db_schema = config.get('db_schema')

    from swagger_server.models_local.base import Base
    # fix-up the postgres schema:
    Base.metadata.schema = db_schema if db_connection.startswith('postgres') else None

    from swagger_server.models_local import _models

    logger.info("Dropping database tables.")
    if db_connection.startswith('postgres'):
        logger.info("Dropping schema {}.".format(db_schema))
        engine.execute("DROP SCHEMA IF EXISTS {} CASCADE".format(db_schema))
    else:
        Base.metadata.drop_all(engine)


def create(config, engine, logger):
    db_connection = config.get('db_connection')
    db_schema = config.get('db_schema')

    from swagger_server.models_local.base import Base
    # fix-up the postgres schema:
    Base.metadata.schema = db_schema if db_connection.startswith('postgres') else None

    from swagger_server.models_local import _models

    if config.do_create_database:
        logger.info("Checking if database already exists.")
        if util.database_exists(db_connection):
            logger.info("Database exists, skipping creation")
        else:
            util.create_database(db_connection)
            logger.info("Created new database at '{}'".format(db_connection))

    logger.info("Creating database model at uri '{}'".format(db_connection))
    if db_connection.startswith('postgres'):
        logger.info("Database type is postgres. Creating schema {}.".format(db_schema))
        engine.execute("CREATE SCHEMA IF NOT EXISTS {}".format(db_schema))
    logger.info("Creating database tables.")
    Base.metadata.create_all(engine)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Create the RAS party database")
    parser.add_argument('-c', '--config',
                        metavar='<config-file-path>',
                        type=str,
                        help="Path to the DB configuration file",
                        required=True)

    parser.add_argument('-e', '--environment',
                        metavar='<environment-name>',
                        type=str,
                        help="Name of the config section to use",
                        required=True)

    args = parser.parse_args()

    config = ConfigParser()
    config._interpolation = ExtendedInterpolation()
    config.read(args.config)

    config = config[args.environment]

    logger = ons_logger.create(config)

    engine = create_engine(config.get('db_connection'), convert_unicode=True)

    if config.get('db_drop').lower() in ['true', 'yes']:
        drop(config, engine, logger)
    create(config, engine, logger)
