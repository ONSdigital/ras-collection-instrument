#!/bin/bash
if ! [ -a .build-test ] ; then
	echo "Creating Virtual Environment"
	virtualenv .build-test -p python3
fi
source .build-test/bin/activate
pip -q install -r test-requirements.txt
pytest --cov=swagger_server/controllers --cov-report term-missing
