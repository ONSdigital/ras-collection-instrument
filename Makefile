build:
	pipenv install --dev

build-docker:
	docker build .

build-kubernetes:
	docker build -f _infra/docker/Dockerfile .

lint:
# remove -i 70624 once flask-cors is updated beyond v4.0.1 to solve vulnerability
# remove -i 70612 once jinja2 is updated beyond v3.1.4 to solve vulnerability
	pipenv check ./application ./tests -i 70612 -i 70624
	pipenv run isort .
	pipenv run black --line-length 120 .
	pipenv run flake8 ./application ./tests

test: lint
	pipenv run tox

start:
	pipenv run python run.py
