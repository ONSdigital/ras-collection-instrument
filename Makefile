.PHONY: build build-docker build-kubernetes start-db lint lint-check test test-html start
DOCKER ?= $(shell if [ "$$(uname -m)" = "arm64" ]; then echo podman; else echo docker; fi)

build:
	pipenv install --dev

build-docker:
	$(DOCKER) build .

build-kubernetes:
	$(DOCKER) build -f _infra/docker/Dockerfile .

# The postgres image version is read from _infra/postgres-image, which CI uses too.
start-db:
	$(DOCKER) compose --env-file _infra/postgres-image up -d db

lint:
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8 .

lint-check:
	pipenv run isort . --check-only
	pipenv run black --line-length 120 --check .
	pipenv run flake8 .

test: lint-check
	APP_SETTINGS=TestingConfig pipenv run pytest tests --cov=application --cov-report term-missing

test-html: lint-check
	APP_SETTINGS=TestingConfig pipenv run pytest tests --cov=application --cov-report html --cov-report term-missing

start:
	pipenv run python run.py
