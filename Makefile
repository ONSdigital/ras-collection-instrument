build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
	pipenv run flake8 ./application ./tests
	pipenv check ./application ./tests
	pipenv run isort .

test: lint
	pipenv run tox

start:
	pipenv run python run.py
