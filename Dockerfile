FROM python:3.6
WORKDIR /app
COPY . /app
EXPOSE 8082
RUN pip3 install pipenv==8.3.1 && pipenv install --deploy --system
ENV PYTHON_PATH=swagger_server
ENTRYPOINT ["python", "-m","swagger_server"]
