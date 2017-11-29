from flask_cors import CORS
from ras_common_utils.ras_config import ras_config
from ras_common_utils.ras_config.flask_extended import Flask
from ras_common_utils.ras_database.ras_database import RasDatabase
from ras_common_utils.ras_logger.ras_logger import configure_logger
from structlog import get_logger
from ras_common_utils.ras_error.ras_error import RasError
from flask import jsonify
log = get_logger()


def create_app(config):
    # create and configure the Flask application
    app = Flask(__name__)
    app.config.from_ras_config(config)

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, RasError):
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
        else:
            response = jsonify({'errors': [str(error)]})
            response.status_code = 500
        return response

    # register view blueprints
    from application.views.survey_responses_view import survey_responses_view
    app.register_blueprint(survey_responses_view, url_prefix='/survey_response-api/v1')
    from application.views.collection_instrument_view import collection_instrument_view
    app.register_blueprint(collection_instrument_view, url_prefix='/collection-instrument-api/1.0.2')
    from application.views.info_view import info_view
    app.register_blueprint(info_view)

    CORS(app)
    return app


def initialise_db(app):
    # Initialise the database with the specified SQLAlchemy model
    collection_instrument_database = RasDatabase.make(model_paths=['application.models.models'])
    db = collection_instrument_database('ras-ci-db', app.config)
    app.db = db


if __name__ == '__main__':

    config_path = 'config/config.yaml'
    config = ras_config.from_yaml_file(config_path)
    configure_logger(config.service)

    app = create_app(config)
    initialise_db(app)
    scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])

    app.run(debug=app.config['DEBUG'], host=host, port=port)
