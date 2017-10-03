FROM python:3.6
WORKDIR /app
COPY . /app
EXPOSE 8082
RUN pip3 install -r requirements.txt --upgrade
ENV PYTHON_PATH=swagger_server
ENTRYPOINT ["python3", "-m","swagger_server"]
