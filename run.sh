#!/bin/bash

# Use the current directory name to locate/name the image and container:
name=${PWD##*/}

# Delete the container if running:
docker rm -f $name

# Get the network name:
network=`docker network ls --filter name=ras -q`

# Run a container and capture the ID of the container:
docker run -d --net $network -p "8070:8080" -p "8001:8000" -e spring.datasource.url=jdbc:postgresql://postgres:5432/postgres --name $name $name
Echo Tailing Docker log for $name. Ctrl-C will stop tailing but will leave the container running.
docker logs -f $name
