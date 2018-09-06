"""This is a duplicate of run.py, with minor modifications to support gunicorn execution."""
from run import create_app

app = create_app()

scheme, host, port = app.config['SCHEME'], app.config['HOST'], int(app.config['PORT'])
