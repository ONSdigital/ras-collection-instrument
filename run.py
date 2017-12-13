import logging
from ras_common_utils.ras_database.ras_database import RasDatabase
from structlog import wrap_logger
from flask import Flask


def create_app():
    # create and configure the Flask application
    app = Flask(__name__)
    app.config.from_object('config.Config')
    return app


def initialise_db(app):
    # Initialise the database with the specified SQLAlchemy model
    collection_instrument_database = RasDatabase.make(model_paths=['application.models.models'])
    db = collection_instrument_database('ras-ci-db', app.config)
    app.db = db

logger = wrap_logger(logging.getLogger(__name__))

if __name__ == '__main__':
    app = create_app()
    initialise_db(app)
    scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])

    app.run(debug=app.config['DEBUG'], host=host, port=port)
