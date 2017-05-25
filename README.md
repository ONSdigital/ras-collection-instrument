# Collection Instruments API Microservice
[![Build Status](https://travis-ci.org/ONSdigital/ras-collection-instrument-demo.svg?branch=master)](https://travis-ci.org/ONSdigital/ras-collection-instrument-demo) 
[![codecov](https://codecov.io/gh/onsdigital/ras-collection-instrument-demo/branch/master/graph/badge.svg)](https://codecov.io/gh/onsdigital/ras-collection-instrument-demo)

This server contains auto-generated code, please refer to the 
[ras-swagger-codegen](https://github.com/ONSdigital/ras-swagger-codegen) project, before making changes 
to this repository.

## Overview

This repository implements REST endpoints for the RAS Collection Instrument based on the Swagger API 
definition [here](https://app.swaggerhub.com/apis/oddjobz/collection-instrument-api/1.0.1). 
If you need to make a change to the REST interface, please start by changing the API spec, then regenerate 
the code using the code generator in the repository described above.

![ons_startup.png](ons_startup.png)

#### Your changes

Changes should only be made to code in the following folders;

* swagger\_server/controller\_slocal
* swagger\_server/tests\_local
* README.md

Anything else is at risk of being overwritten.

## Running Locally

To run locally from the root of your repository, run;

```bash
./run.sh
```

On your first attempt it will build a virtual environment in .build, which will take 30 seconds or so, on 
subsequent runs this will be almost instantaneous. By default the service will be available 
on **http://localhost:8080/collection-instrument-api/1.0.1/ui**.

### Uploading files from the command line

From the **scripts** folder, you should be able to run;

```bash
./upload.py local id_example 30
```
To upload files to the current CF installation, use **live** instead of local. Note that you will need to 
create a batch with Survey **BRES** and CE of **2017** using the UI link above, otherwise the upload will yield 
a 'no such batch' error. (this will upload *30* dummy files)

#### Testing

To run the unit tests and code coverage, run the test.sh script an you should get something like this;

```bash
$ ./test.sh 
======================================================= test session starts =======================================================
platform linux -- Python 3.5.2+, pytest-3.0.7, py-1.4.33, pluggy-0.4.0
rootdir: /home/gareth/Code/ONS/ras-repos/ras-collection-instrument-demo, inifile:
plugins: cov-2.5.1
collected 23 items 

swagger_server/test/test_cec_controller.py .....
swagger_server/test/test_ciupload_controller.py .......
swagger_server/test/test_respondent_controller.py ...
swagger_server/test/test_static_controller.py .
swagger_server/test_local/test_ciupload_controller.py .......

----------- coverage: platform linux, python 3.5.2-final-0 -----------
Name                                                        Stmts   Miss  Cover   Missing
-----------------------------------------------------------------------------------------
swagger_server/controllers_local/ciupload_controller.py        38      6    84%   55, 91, 110-113
swagger_server/controllers_local/lib.py                        52      0   100%
swagger_server/controllers_local/respondent_controller.py       0      0   100%
swagger_server/controllers_local/static_controller.py           6      0   100%
-----------------------------------------------------------------------------------------
TOTAL                                                          96      6    94%


==================================================== 23 passed in 6.35 seconds ====================================================
```

