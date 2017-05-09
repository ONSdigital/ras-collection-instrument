FROM python:2
MAINTAINER David Carboni

WORKDIR /app
ADD application ./application
ADD requirements.txt ./

RUN pip install -r requirements.txt

ENTRYPOINT python application/app.py
