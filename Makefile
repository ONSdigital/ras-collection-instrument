build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8 ./application ./tests

test: lint
	pipenv run tox

start:
	pipenv run python run.py
