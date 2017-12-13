import os

from flask import Flask
from flask_cors import CORS

from application.logger_config import logger_initial_config


app = Flask(__name__)

app_config = 'config.{}'.format(os.environ.get('APP_SETTINGS', 'Config'))
app.config.from_object(app_config)

logger_initial_config(service_name='response-operations-ui', log_level=app.config['LOGGING_LEVEL'])

# register view blueprints
from application.views.survey_responses_view import survey_responses_view

app.register_blueprint(survey_responses_view, url_prefix='/survey_response-api/v1')
from application.views.collection_instrument_view import collection_instrument_view

app.register_blueprint(collection_instrument_view, url_prefix='/collection-instrument-api/1.0.2')
from application.views.info_view import info_view

app.register_blueprint(info_view)

CORS(app)
