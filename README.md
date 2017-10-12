# RAS Collection Instrument

[![Build Status](https://travis-ci.org/ONSdigital/ras-collection-instrument.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-collection-instrument) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/e4cee89df456488c95c26c10a07e4f97)](https://www.codacy.com/app/ONSDigital/ras-collection-instrument?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/ras-collection-instrument&amp;utm_campaign=Badge_Grade)

## Overview
This is the RAS Collection Instrument micro-service, responsible for the uploading of collection exercises and instruments

The API is specified [here](./API.md).


## Tests
To run the tests with [tox], install tox, then simply run the command `pipenv run tox` in the root of the project.
tox will create a unique virtualenv, run the unit tests with py.test, then run flake8 coverage.

To install and run:
``` bash
pipenv run python run.py
```

To test the service is up:

```
curl http://localhost:8082/info
```

The database will automatically be created when starting the application.

## Upload test collection instruments
Navigate to /developer_scripts and run import.py, answer the prompts on the command line


