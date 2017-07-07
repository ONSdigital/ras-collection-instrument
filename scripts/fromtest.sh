#!/bin/bash
if ! [ -a .build ] ; then
	echo "Creating Virtual Environment"
	virtualenv .build -p python3
fi
source .build/bin/activate
pip install -i https://testpypi.python.org/pypi ons_ras_common --upgrade
