# import structlog
# import os
# from ras_common_utils.ras_logger.ras_logger import configure_logger
#
# from run import create_app, initialise_db
#
# # This is a duplicate of run.py, with minor modifications to support gunicorn execution.
#
# logger = structlog.get_logger()
#
# config_path = 'config.py'
# config = os.environ['APP_SETTINGS'] = 'Config'
#
# app = create_app()
# configure_logger(app.config)
# logger.debug("Created Flask application.")
#
# initialise_db(app)
#
# scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])
