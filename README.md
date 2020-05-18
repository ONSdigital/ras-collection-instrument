# RAS Collection Instrument

[![Build Status](https://travis-ci.org/ONSdigital/ras-collection-instrument.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-collection-instrument) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/e4cee89df456488c95c26c10a07e4f97)](https://www.codacy.com/app/ONSDigital/ras-collection-instrument?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=ONSdigital/ras-collection-instrument&amp;utm_campaign=Badge_Grade)

## Overview

This is the RAS Collection Instrument micro-service, responsible for the uploading of collection exercises and instruments

The API is specified [here](./API.md).

## Environment

This requires pipenv to be installed:

```bash
pip install pipenv
```

## Tests

To run the tests a rabbitmq and database server is required. The tox script creates and runs these dependencies inside Docker containers, which are destroyed after the unit tests are run.

```bash
pipenv install --dev
pipenv run tox
```

To run the service with the required dependencies:

```bash
docker-compose up -d db rabbitmq
pipenv run python run.py
```

To test the service is up:

```bash
curl http://localhost:8082/info
```

The database will automatically be created when starting the application.

## Docker

To run the service in a Docker container a Compose script is included:

```bash
docker-compose up -d
```

## Configuration

Environment variables available for configuration are listed below:

| Environment Variable         | Description                                                   | Default
|------------------------------|---------------------------------------------------------------|-------------------------------
| MAX_UPLOAD_FILE_NAME_LENGTH  | Maximum length of file names | 50
| LOGGING_LEVEL                | Level of the logger | INFO
| JSON_SECRET_KEYS             | Json representation of keys | None
| ONS_CRYPTOKEY                | A key | None
| SECURITY_USER_NAME           | Username the client uses to authenticate with other apis | admin
| SECURITY_USER_PASSWORD       | Password the client uses to authenticate with other apis | secret
| COLLECTION_EXERCISE_SCHEMA   | Database number for the redis instance | application/schemas/collection_instrument_schema.json
| CASE_URL                     | URL for the case service | 'http://localhost:8171'
| COLLECTION_EXERCISE_PROTOCOL | Protocol used for collection exercise service uri | 'http'
| COLLECTION_EXERCISE_HOST     | Host address used for collection exercise uri | 'localhost'
| COLLECTION_EXERCISE_PORT     | Port used for collection exercise uri | 8145
| SURVEY_SERVICE_URL           | URL for the survey service | 'http://localhost:8080'
| PARTY_URL                    | URL for the party service | 'http://localhost:8081'

These are set in [config.py](config.py)

## Upload test collection instruments

Navigate to /developer_scripts and run import.py, answer the prompts on the command line
