#!/bin/bash
if ! [ -a .build ] ; then
	echo "Creating Virtual Environment"
	virtualenv .build -p python3
fi
source .build/bin/activate
pip3 -q install -r requirements.txt
PYTHONPATH=swagger_server python3 -m swagger_server
