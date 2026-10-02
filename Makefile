.PHONY: init reset api migrate test

init:
	python environment/scripts/init_db.py

reset:
	bash environment/scripts/seed_db.sh

api:
	cd environment/api && go run .

migrate:
	python environment/migrate.py

test:
	cd environment/api && go test ./...
	TOWER_PROJECT_ROOT=environment python -m pytest -q tests/test_outputs.py