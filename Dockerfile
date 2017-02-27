FROM python:2
MAINTAINER David Carboni

WORKDIR /app
ADD ras-collection-instrument ./ras-collection-instrument
ADD requirements.txt ./

RUN pip install -r requirements.txt

ENTRYPOINT python ras-collection-instrument/app.py
