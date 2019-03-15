FROM python:3.6-slim

WORKDIR /app
COPY . /app
EXPOSE 8002
RUN apt-get update -y && apt-get install -y python-pip
RUN pip3 install pipenv==8.3.1 && pipenv install --deploy --system

RUN groupadd --gid 992 collectioninstrumentsvc && \
    useradd --create-home --system --uid 992 --gid collectioninstrumentsvc collectioninstrumentsvc
USER collectioninstrumentsvc

ENTRYPOINT ["python3"]
CMD ["run.py"]
