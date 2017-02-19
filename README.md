# ras-collection-instrument

(1.) ./build at /ras-compose as normal
(2.) ./run at /ras-compose as normal
NOTE: ras-collection-instrument container will start, fail then stop if the ras_collection_instrument schema has not been created. Therefore...
(3.) connect to postgres via PGAdmin and run in ras_collection_instrument_D0001_initial_build.sql
(4.) docker start rascompose_ras-collection-instrument_1 (simply restart this stopped container)
(5.) docker logs -f rascompose_ras-collection-instrument_1 (check the service starts as expected with no errors)

Once started, the following endpoints can be requested

http://localhost:8070/servicestatus [ json text of service info inc. name, version, build / deploy dates ]
http://localhost:8070/collectioninstrument [ should return an arrary of application/json of all CIs HTTP 200 ]
http://localhost:8070/collectioninstrument/id/1 [ should return application/json for CI id 1 HTTP 200 ]
http://localhost:8070/collectioninstrument/id/999 [ non existent CI should return HTTP 404 ]

Application and springboot logs in container at
/logs/springboot_ras-collectioninstrument.log
/logs/ras-collectioninstrument.log

Key Libraries
-------------
Spring Core: 4.3.5
Spring Boot: 1.4.3
Spring Cloud: 1.1
Logging: log4j2 2.6.2 (over slf4j)
Monitoring: Springboot Actuator
Persistence: Hibernate 5.0.11
JSON databind: jackson 2.8.5