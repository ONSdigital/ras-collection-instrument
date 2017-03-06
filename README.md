[![Build Status](https://travis-ci.org/ONSdigital/ras-collection-instrument.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-collection-instrument)


# ras-collection-instrument (Python)

## Gettingt started with the Python version of the CI micro service:

** Note: This explains how to use the Collection Instrument micro service using the Python-Flask based micro
** service container.

  1. [./build](https://github.com/ONSdigital/ras-compose/blob/master/build.sh) at [ras-compose](https://github.com/ONSdigital/ras-compose) as normal
  2. [./run](https://github.com/ONSdigital/ras-compose/blob/master/run.sh) at [ras-compose](https://github.com/ONSdigital/ras-compose) as normal
NOTE: ras-collection-instrument container will start, fail then stop if the ras_collection_instrument schema has not been created. Therefore...
  3. connect to postgres via PGAdmin and run in ras_collection_instrument_D0001_initial_build.sql e.g.: 
    `psql -h localhost -p 5431 -U postgres -a -f ras_collection_instrument_D0001_initial_build.sql`
  4. docker start rascompose_ras-collection-instrument_1 (simply restart this stopped container)
  5. docker logs -f rascompose_ras-collection-instrument_1 (check the service starts as expected with no errors)

Once started, the following endpoints can be requested

  * [http://localhost:8070/servicestatus](http://localhost:8070/servicestatus) [ json text of service info inc. name, version, build / deploy dates ]
  * [http://localhost:8070/collectioninstrument](http://localhost:8070/collectioninstrument) [ should return an arrary of application/json of all CIs HTTP 200 ]
  * [http://localhost:8070/collectioninstrument/id/1](http://localhost:8070/collectioninstrument/id/1) [ should return application/json for CI id 1 HTTP 200 ]
  * [http://localhost:8070/collectioninstrument/id/999](http://localhost:8070/collectioninstrument/id/999) [ non existent CI should return HTTP 404 ]

Application and springboot logs in container at:

  * /logs/springboot_ras-collectioninstrument.log
  * /logs/ras-collectioninstrument.log

## Key Libraries



## Running Pylint Checker

The pylint checker is used to statistically analyse code for a number of common coding errors and against pep8 standards.
This means that we can have a more automated way of measuring code quality. To run this from the project directory we need
to specify our config file needed to analyse our code. We have modified our checker to not check things like 'line length'
since this is pointless with modern screens being so big.

Running pylint from the command line is done with:

  /> pylint --rcfile=.pylint ras-collection-instrument/app.py


 
