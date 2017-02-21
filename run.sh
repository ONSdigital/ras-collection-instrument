#!/bin/bash

# Delete the container if running:
docker rm -f ras-collection-instrument

# Get the network name:
network=`docker network ls --filter name=ras -q`

# Run a container and capture the ID of the container:
docker run -d --net $network -p "8070:8080" -p "8001:8000" --name ras-collection-instrument ras-collection-instrument
