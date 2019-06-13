FROM python:3.6-slim

RUN apt-get update && apt-get install -y build-essential curl
RUN pip install pipenv

WORKDIR /app
EXPOSE 8002
CMD ["python", "run.py"]

HEALTHCHECK --interval=1m30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8002/info || exit 1

COPY . /app
RUN pipenv install --deploy --system