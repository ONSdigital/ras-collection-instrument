# RAS Collection Instrument

This is the RAS Collection Instrument micro-service, responsible for the uploading of collection exercises and instruments. It can also be used to download collection instruments as .xlsx files, and allows for the searching of collection instruments via search filters.
This service has the ability to link and unlink collection exercises with collection instruments. The relationship between exercises and instruments is one-to-many, so one collection exercise can have multiple collection instruments.
Each collection instrument in the JSON schema has a sample unit reference, type, and summary ID, as well as additional attributes.
This service commmunicates primarily with the collection exercise service, as well as the party, case, and survey services.

Collection instruments are stored in an instrument table with the following fields:

type = the type of the collection exercise (i.e. SEFT, EQ, etc.)
instrument_id = the UUID for the instrument
stamp = the timestamp showing when the collection instrument was created
survey_id = the UUID of the associated survey
classifiers = the survey classifiers
survey = the survey itself
seft_file = the instrument's seft file

Three different endpoint views exist: `/collectioninstrument`, which is used for the majority of the endpoints, as well as `/survey_responses` and `/info`.

When a collection instrument is uploaded for a collection exercise it writes a message onto the Seft.Instruments queue for the rm-collection-exercise service
When a SEFT survey response is uploaded, it writes a message onto the Seft.Responses queue for sdx-seft-consumer service

## Environment

This requires pipenv to be installed:

```bash
pip install pipenv
```

## Tests

To run the tests a database server is required. The tox script creates and runs these dependencies inside Docker containers, which are destroyed after the unit tests are run.

```bash
pipenv install --dev
pipenv run tox
```

To run the service with the required dependencies:

```bash
docker-compose up -d db -f _infra/docker/Dockerfile
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
docker-compose up -d -f _infra/docker/Dockerfile
```

## Configuration

Environment variables available for configuration are listed below:

| Environment Variable        | Description                                              | Default                                               |
|-----------------------------|----------------------------------------------------------|-------------------------------------------------------|
| MAX_UPLOAD_FILE_NAME_LENGTH | Maximum length of file names                             | 50                                                    |
| LOGGING_LEVEL               | Level of the logger                                      | INFO                                                  |
| ONS_CRYPTOKEY               | A key used by the Cryptographer                          | None                                                  |
| SECURITY_USER_NAME          | Username the client uses to authenticate with other apis | admin                                                 |
| SECURITY_USER_PASSWORD      | Password the client uses to authenticate with other apis | secret                                                |
| COLLECTION_EXERCISE_SCHEMA  | Location of the collection instrument schema             | application/schemas/collection_instrument_schema.json |
| CASE_URL                    | URL for the case service                                 | 'http://localhost:8171'                               |
| COLLECTION_EXERCISE_URL     | URL for the collection exercise service                  | 'http://localhost:8145'                               |
| SURVEY_SERVICE_URL          | URL for the survey service                               | 'http://localhost:8080'                               |
| PARTY_URL                   | URL for the party service                                | 'http://localhost:8081'                               |



These are set in [config.py](config.py)

## Upload test collection instruments

Navigate to /developer_scripts and run import.py, answer the prompts on the command line

## Suggestions for improvements

* The `collection_instrument_schema` has two seemingly identical attribute fields: `formType` and `formtype`.
* Apropos the previous point, many of the attributes in the schema have unclear names and purposes, like `entname1/2/3` and `runame1/2/3`, among others. The schema should be redesigned, or have more specific documentation.
* A couple of the endpoints have fairly useless functionality. For example, all the `/collectioninstrument/count` endpoint does is return the number of collection instruments. Why is this something the service needs to do? Could this not be accomplished by a database query?
* Given the service's heavy reliance on collection exercises, could this service not be combined with the collection exercise service during the ras-rm redesign?
