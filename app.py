import structlog
from ras_common_utils.ras_config import ras_config
from ras_common_utils.ras_logger.ras_logger import configure_logger

from run import create_app, initialise_db

# This is a duplicate of run.py, with minor modifications to support gunicorn execution.

logger = structlog.get_logger()

config_path = 'config/config.yaml'
config = ras_config.from_yaml_file(config_path)

app = create_app(config)
configure_logger(app.config)
logger.debug("Created Flask application.")

initialise_db(app)

scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])
