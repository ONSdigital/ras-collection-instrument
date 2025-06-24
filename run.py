import logging
import os

import structlog
from alembic import command
from alembic.config import Config
from flask import Flask
from flask_cors import CORS
from retrying import RetryError, retry
from sqlalchemy import column, create_engine, text
from sqlalchemy.exc import DatabaseError, ProgrammingError
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.sql import exists, select

from application.logger_config import logger_initial_config

logger = structlog.wrap_logger(logging.getLogger(__name__))


def create_app(config=None, init_db=True):
    # create and configure the Flask application
    app = Flask(__name__)
    app.name = "ras-collection-instrument"
    config_name = config or os.environ.get("APP_SETTINGS", "Config")
    app_config = f"config.{config_name}"
    app.config.from_object(app_config)

    # register view blueprints

    from application.views.collection_instrument_view import collection_instrument_view

    app.register_blueprint(collection_instrument_view, url_prefix="/collection-instrument-api/1.0.2")

    from application.views.info_view import info_view

    app.register_blueprint(info_view)

    from application.views.registry_instrument_view import registry_instrument_view

    app.register_blueprint(registry_instrument_view, url_prefix="/collection-instrument-api/1.0.2")

    from application.error_handlers import error_blueprint

    app.register_blueprint(error_blueprint)

    CORS(app)

    logger_initial_config(service_name="ras-collection-instrument", log_level=app.config["LOGGING_LEVEL"])
    logger.info("Logging configured", log_level=app.config["LOGGING_LEVEL"])

    if init_db:
        try:
            initialise_db(app)
        except RetryError:
            logger.exception("Failed to initialise database")
            exit(1)
    else:
        logger.debug("Skipped initialising database")

    logger.info("App setup complete", config=config_name)

    return app


def create_database(db_connection, db_schema):
    from application.models import models

    engine = create_engine(db_connection)
    session_factory = sessionmaker(bind=engine)
    session = scoped_session(session_factory)
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session

    if db_connection.startswith("postgres"):
        for t in models.Base.metadata.sorted_tables:
            t.schema = db_schema

        schemata_exists = exists(
            select(column("schema_name"))
            .select_from(text("information_schema.schemata"))
            .where(text(f"schema_name = '{db_schema}'"))
        )

        alembic_cfg = Config("alembic.ini")

        if not session().query(schemata_exists).scalar():
            logger.info("Creating schema ", db_schema=db_schema)
            session().execute(text(f"CREATE SCHEMA {db_schema}"))
            session().commit()
            logger.info("Creating database tables.")
            models.Base.metadata.create_all(engine)
            # If the db is created from scratch we don't need to update with alembic,
            # however we do need to record (stamp) the latest version for future migrations
            command.stamp(alembic_cfg, "head")
        else:
            logger.info("Updating database with Alembic")
            command.upgrade(alembic_cfg, "head")

    else:
        logger.info("Creating database tables")
        models.Base.metadata.create_all(engine)

    logger.info("Ok, database tables have been created")
    return engine


def retry_if_database_error(exception):
    logger.error(exception)
    return isinstance(exception, DatabaseError) and not isinstance(exception, ProgrammingError)


@retry(retry_on_exception=retry_if_database_error, wait_fixed=2000, stop_max_delay=30000, wrap_exception=True)
def initialise_db(app):
    # TODO: this isn't entirely safe, use a get_db() lazy initializer instead...
    app.db = create_database(app.config["DATABASE_URI"], app.config["DATABASE_SCHEMA"])


if __name__ == "__main__":
    app = create_app()

    scheme, host, port = app.config["SCHEME"], app.config["HOST"], int(app.config["PORT"])

    app.run(debug=app.config["DEBUG"], host=host, port=port)
