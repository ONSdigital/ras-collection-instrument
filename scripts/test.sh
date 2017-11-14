#!/bin/bash
ONS_ENV=travis py.test --cov=swagger_server/controllers --cov-report term-missing
