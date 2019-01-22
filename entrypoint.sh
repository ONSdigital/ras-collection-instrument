#!/usr/bin/env bash

exec gunicorn app:app --bind 0.0.0.0:8002 --workers $GUNICORN_WORKERS --worker-class gevent --keep-alive 2 --timeout 30