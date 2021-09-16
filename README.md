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
docker-compose up -d db 
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

| Environment Variable                | Description                                                   | Default
|-------------------------------------|---------------------------------------------------------------|-------------------------------
| MAX_UPLOAD_FILE_NAME_LENGTH         | Maximum length of file names | 50
| LOGGING_LEVEL                       | Level of the logger | INFO
| JSON_SECRET_KEYS                    | Json representation of keys | None
| ONS_CRYPTOKEY                       | A key used by the Cryptographer | None
| SECURITY_USER_NAME                  | Username the client uses to authenticate with other apis | admin
| SECURITY_USER_PASSWORD              | Password the client uses to authenticate with other apis | secret
| COLLECTION_EXERCISE_SCHEMA          | Location of the collection instrument schema | application/schemas/collection_instrument_schema.json
| CASE_URL                            | URL for the case service | 'http://localhost:8171'
| COLLECTION_EXERCISE_URL             | URL for the collection exercise service | 'http://localhost:8145'
| SURVEY_SERVICE_URL                  | URL for the survey service | 'http://localhost:8080'
| PARTY_URL                           | URL for the party service | 'http://localhost:8081'



These are set in [config.py](config.py)

## Upload test collection instruments

Navigate to /developer_scripts and run import.py, answer the prompts on the command line

## Suggestions for improvements

* The `collection_instrument_schema` has two seemingly identical attribute fields: `formType` and `formtype`.
* Apropos the previous point, many of the attributes in the schema have unclear names and purposes, like `entname1/2/3` and `runame1/2/3`, among others. The schema should be redesigned, or have more specific documentation.
* A couple of the endpoints have fairly useless functionality. For example, all the `/collectioninstrument/count` endpoint does is return the number of collection instruments. Why is this something the service needs to do? Could this not be accomplished by a database query?
* Given the service's heavy reliance on collection exercises, could this service not be combined with the collection exercise service during the ras-rm redesign?

## Updates GNU
* The system now uses GNUPG to encrypt seft messages which is controlled by the saveSeftInGcp flagged stored in the values.yml file
* Due to the version of GNUPG current used in Docker (as of 03/06/2021 BST/UK) (gpg (GnuPG) 2.2.12 libgcrypt 1.8.4) it does NOT support an email as a recipient, you need to use the fingerprint
* if you receive a binary public key you MUST convert it to ascii with armor. use the following command.
```
 gpg --export -a <  sdx_preprod_binary_key.gpg > sdx_preprod_binary_key.gpg.asc    
```
and load this upto the secret key manager - gnu-public-crypto-key

* to get the fingerprint. the fingerprint will look like 'A8F49D6EE2DE17F03ACF11A9BF16B2EB4DASE991
Also, make sure have an empty local trusted db
```
gpg --with-fingerprint <~/.gnupg/sdx_preprod_binary_key.gpg.asc
```

* important to check that the subkey next to the fingerprint has not expired and be aware that some public key have been unable and it is worth sanity checking them on the command line

* within the project there is a development public/private gnupg key. However if you wish to create your own 
```
gpg --full-generate-key
gpg --list-secret-keys --keyid-format=long
```
The current values provided are
```
gpg --list-secret-keys --keyid-format=long
------------------------------------
sec   ed25519/3CB9DD17EFF9948B 2021-06-10 [SC]
      C46BB0CB8CEBBC20BC07FCA83CB9DD17EFF9948B
uid                 [ultimate] ONS RAS Dev Team (USE FOR DEVELOPMENT ONLY) <dev@example.com>
ssb   cv25519/ED1B7A3EADF95687 2021-06-10 [E]
```
Then export via
```
gpg --armor --export ED1B7A3EADF95687
```
current saved exported  public private keys are dev-public-key.asc dev-private-key.asc
The private key is only supplied for testing decryption
passphase if needed is PASSWORD1