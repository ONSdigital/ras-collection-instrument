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

lint-check:
	pipenv run flake8 ./application ./tests
	pipenv check ./application ./tests
	pipenv run isort . --check-only -v

test: lint-check
	pipenv run tox

start:
	pipenv run python run.py
