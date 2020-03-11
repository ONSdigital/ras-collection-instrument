build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	pipenv run flake8 ./application ./tests
# TEMPORARILY disable pipenv check, pending resolution of pipenv bugs 2412 and 4147
# TODO: re-enable as soon as possible.
#	pipenv check ./application ./tests

test: lint
	pipenv run tox

start:
	pipenv run python run.py
