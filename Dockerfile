FROM python:3
MAINTAINER David Carboni

WORKDIR /app
ADD *.py ./
ADD requirements.txt ./
CMD pip install -r requirements.txt

ENTRYPOINT python app.py
