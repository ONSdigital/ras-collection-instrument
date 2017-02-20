#!/bin/bash

docker run -it --rm --volume `pwd`:/root --volume $HOME/.gradle:/root/.gradle frekele/gradle gradle clean build
docker build --tag ras-collection-instrument .
