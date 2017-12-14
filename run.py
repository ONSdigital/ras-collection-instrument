import logging
import structlog
from flask import Flask
from flask_cors import CORS
from flask import _app_ctx_stack
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

logger = structlog.wrap_logger(logging.getLogger(__name__))


def create_app():
    # create and configure the Flask application
    app = Flask(__name__)
    app.config.from_object('config.Config')
    CORS(app)
    return app


def create_database(db_connection, db_schema):
    from application.models import models

    engine = create_engine(db_connection, convert_unicode=True)
    session = scoped_session(sessionmaker(), scopefunc=lambda: _app_ctx_stack.__ident_func__())
    session.configure(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    engine.session = session

    # fix-up the postgres schema:
    if db_connection.startswith('postgres'):
        for t in models.Base.metadata.sorted_tables:
            t.schema = db_schema

    logger.info("Creating database with uri '{db_connection}'")
    if db_connection.startswith('postgres'):
        logger.info("Creating schema {db_schema}.")
        engine.execute("CREATE SCHEMA IF NOT EXISTS {db_schema}")
    logger.info("Creating database tables.")
    models.Base.metadata.create_all(engine)
    logger.info("Ok, database tables have been created.")
    return engine


def initialise_db(app):
    # TODO: this isn't entirely safe, use a get_db() lazy initializer instead...
    app.db = create_database(app.config['DATABASE_URI'], app.config['DATABASE_SCHEMA'])

if __name__ == '__main__':
    app = create_app()
    try:
        initialise_db(app)
    except:
        logger.exception('Failed to initialise database')
        exit(1)

    scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])

    app.run(debug=app.config['DEBUG'], host=host, port=port)
