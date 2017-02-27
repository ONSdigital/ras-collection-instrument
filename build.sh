#!/bin/bash

# Use the current directory name to tag the Docker image:
name=${PWD##*/}

docker build --tag $name .
