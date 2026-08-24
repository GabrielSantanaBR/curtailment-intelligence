.PHONY: install install-dev doctor bootstrap run test check frontend-build docker-up docker-down

install:
	python -m pip install -r requirements.txt

install-dev:
	python -m pip install -r requirements-dev.txt

doctor:
	python scripts/dev.py doctor

bootstrap:
	python scripts/dev.py bootstrap

run:
	python scripts/dev.py run

test:
	python scripts/dev.py test

check:
	python scripts/dev.py check

frontend-build:
	cd frontend && npm install && npm run build

docker-up:
	docker compose up --build

docker-down:
	docker compose down
