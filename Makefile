build:
	pipenv install --dev

lint:
	pipenv run flake8 ./application ./tests
	pipenv check ./application ./tests

test: lint
	pipenv run tox

start:
	pipenv run python run.py
