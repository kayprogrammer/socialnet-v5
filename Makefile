ifneq (,$(wildcard ./.env))
include .env
export 
ENV_FILE_PARAM = --env-file .env

endif

build:
	docker-compose up --build -d --remove-orphans

up:
	docker-compose up -d

down:
	docker-compose down

show-logs:
	docker-compose logs

serv:
	litestar run --reload

init-db:
	aerich init-db

mmig: ## Run migrations. Use "make mmig" or "make mmig message='App migrated'"
	aerich migrate ${if $(message),--name ${message}}


mig:
	aerich upgrade

init:
	python initials/initial_data.py

tests:
	pytest --disable-warnings -vv -x

reqm:
	pip install -r requirements.txt

ureqm:
	pip freeze > requirements.txt