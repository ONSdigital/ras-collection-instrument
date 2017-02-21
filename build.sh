#!/bin/bash

# Use the current directory name to tag the Docker image:
name=${PWD##*/}

gradle clean build
docker build --tag $name .
