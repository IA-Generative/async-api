.PHONY: help build run clean install test lint format

# Variables
IMAGE_NAME := python-worker
CONTAINER_NAME := async-worker-demo
BROKER_URL := amqp://localhost:5672

help: ## Affiche cette aide
	@echo "Commandes disponibles:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Installe le package en mode développement
	pip install -e .

install-dev: ## Installe les dépendances de développement
	pip install -e ".[dev]"

build: ## Construit l'image Docker
	docker build -t $(IMAGE_NAME) .

run: ## Lance le conteneur Docker
	docker run --rm --name $(CONTAINER_NAME) \
		-e BROKER_URL="$(BROKER_URL)" \
		-e IN_QUEUE_NAME="in_queue_python" \
		-e OUT_QUEUE_NAME="example_out_queue" \
		-e WORKER_CONCURRENCY="3" \
		-p 8000:8000 \
		$(IMAGE_NAME)

run-detached: ## Lance le conteneur Docker en arrière-plan
	docker run -d --name $(CONTAINER_NAME) \
		-e BROKER_URL="$(BROKER_URL)" \
		-e IN_QUEUE_NAME="in_queue_python" \
		-e OUT_QUEUE_NAME="example_out_queue" \
		-e WORKER_CONCURRENCY="3" \
		-p 8000:8000 \
		$(IMAGE_NAME)

stop: ## Arrête le conteneur Docker
	docker stop $(CONTAINER_NAME) || true

clean: ## Supprime les conteneurs et images
	docker stop $(CONTAINER_NAME) || true
	docker rm $(CONTAINER_NAME) || true
	docker rmi $(IMAGE_NAME) || true

logs: ## Affiche les logs du conteneur
	docker logs -f $(CONTAINER_NAME)

shell: ## Ouvre un shell dans le conteneur
	docker exec -it $(CONTAINER_NAME) /bin/bash

test: ## Lance les tests
	pytest tests/ -v

test-cov: ## Lance les tests avec couverture
	pytest tests/ -v --cov=src/mic_worker --cov-report=term-missing

test-unit: ## Lance seulement les tests unitaires
	pytest tests/test_typed.py tests/test_health_check.py tests/test_worker_runner.py -v

test-integration: ## Lance seulement les tests d'intégration
	pytest tests/test_integration.py -v

lint: ## Lance le linting avec ruff
	ruff check .
	ruff format --check .

format: ## Formate le code avec ruff
	ruff format .
	ruff check --fix .

health-check: ## Vérifie le health check du conteneur
	curl -f http://localhost:8000/ && echo "✅ Health check OK" || echo "❌ Health check failed"
