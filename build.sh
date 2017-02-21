#!/bin/bash

gradle clean build
docker build --tag ras-collection-instrument .
