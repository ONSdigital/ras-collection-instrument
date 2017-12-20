import logging
import os
import structlog

from flask import Flask, _app_ctx_stack
from flask_cors import CORS
from json import loads
from retrying import RetryError
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from application.logger_config import logger_initial_config

logger = structlog.wrap_logger(logging.getLogger(__name__))


def create_app():
    # create and configure the Flask application
    app = Flask(__name__)
    app_config = 'config.{}'.format(os.environ.get('APP_SETTINGS', 'Config'))
    app.config.from_object(app_config)

    # register view blueprints
    from application.views.survey_responses_view import survey_responses_view
    app.register_blueprint(survey_responses_view, url_prefix='/survey_response-api/v1')
    from application.views.collection_instrument_view import collection_instrument_view
    app.register_blueprint(collection_instrument_view, url_prefix='/collection-instrument-api/1.0.2')
    from application.views.info_view import info_view
    app.register_blueprint(info_view)
    from application.error_handlers import error_blueprint
    app.register_blueprint(error_blueprint)

    CORS(app)
    return app


def create_database(db_connection, db_schema):
    from application.models import models

    def current_request():
        return _app_ctx_stack.__ident_func__()

    engine = create_engine(db_connection, convert_unicode=True)
    session = scoped_session(sessionmaker(), scopefunc=current_request)
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session

    # fix-up the postgres schema:
    if db_connection.startswith('postgres'):
        for t in models.Base.metadata.sorted_tables:
            t.schema = db_schema

    logger.info(f"Creating database with uri '{db_connection}'")
    if db_connection.startswith('postgres'):
        logger.info(f"Creating schema {db_schema}.")
        engine.execute(f"CREATE SCHEMA IF NOT EXISTS {db_schema}")
    logger.info("Creating database tables.")
    models.Base.metadata.create_all(engine)
    logger.info("Ok, database tables have been created.")
    return engine


def initialise_db(app):
    # TODO: this isn't entirely safe, use a get_db() lazy initializer instead...
    app.db = create_database(app.config['DATABASE_URI'],
                             app.config['DATABASE_SCHEMA'])


if __name__ == '__main__':
    app = create_app()
    with open(app.config['COLLECTION_EXERCISE_SCHEMA']) as io:
        app.config['COLLECTION_EXERCISE_SCHEMA'] = loads(io.read())

    logger_initial_config(service_name='ras-collection-instrument', log_level=app.config['LOGGING_LEVEL'])

    try:
        initialise_db(app)
    except RetryError:
        logger.exception('Failed to initialise database')
        exit(1)

    scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])

    app.run(debug=app.config['DEBUG'], host=host, port=port)
