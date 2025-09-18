IMAGE_NAME_API=api
IMAGE_NAME_CONSUMER=consumer
IMAGE_NAME_WORKER_PYTHON=worker-python
PYTHONPATH=$(PWD)
API_CONTAINER=api
LISTENER_CONTAINER=listener
CONSUMER_CONTAINER=consumer
WORKER_PYTHON_CONTAINER=worker-python

.PHONY: install-uv install-local lint bump-patch bump-minor \
        up down logs-api logs-listener logs-consumer logs-worker-python \
        build build-api build-consumer build-worker-python \
        migrate stamp-db list-revision upgrade-revision \
        test coverage clean clean-cache help

.DEFAULT_GOAL := help

help: ## Affiche l'aide
	@echo "Usage: make <command>"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-25s\033[0m %s\n", $$1, $$2}'

install: install-uv ## Installation de l'environnement pour du développement local
	@if [ ! -d ".venv" ]; then \
		echo "Synchronisation des dépendances..."; \
		uv sync; \
	else \
		echo "Dépendances déjà synchronisées (suppose .venv existant)"; \
	fi

install-uv: ## Installe uv
	@if ! command -v uv >/dev/null 2>&1; then \
		echo "uv non trouvé, installation..."; \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
	else \
		echo "uv déjà installé"; \
	fi

lint: install ## Lint le code du dépôt avec ruff
	uvx ruff check .

format: install ## Formate le code avec ruff
	uvx ruff format .

bump-patch: ## Bump version patch
	uv run cz bump --increment patch

bump-minor: ## Bump version minor
	uv run cz bump --increment minor

up: ## Lance l'environnement de développement en conteneurs
	docker compose up -d

down: ## Éteint l'environnement de développement en conteneurs
	docker compose down || true

logs: ## Affiche les logs de tous les conteneurs
	docker compose logs -f

logs-api: ## Affiche les logs du conteneur API
	docker compose logs -f api

logs-listener: ## Affiche les logs du conteneur listener
	docker compose logs -f listener

logs-consumer: ## Affiche les logs du conteneur consumer JS
	docker compose logs -f consumer

logs-db: ## Affiche les logs de la base de données
	docker compose logs -f db

logs-rabbitmq: ## Affiche les logs de RabbitMQ
	docker compose logs -f broker

build: build-api build-consumer build-listener ## Lance la construction de toutes les images Docker

build-api: ## Lance la construction de l'image Docker API
	docker compose build api

build-consumer: ## Lance la construction de l'image Docker consumer JS
	docker compose build consumer

build-listener: ## Lance la construction de l'image Docker du listener de l'api
	docker compose build worker-python

migration-stamp-db: ## Change le pointeur alembic à une révision particulière
	@read -p "ID de la révision : " revision; \
	docker compose exec api alembic stamp $$revision

migration-add-revision: ## Crée une nouvelle révision de base de données
	@read -p "Message de révision : " msg; \
	docker compose exec api alembic revision --autogenerate -m "$$msg"

migration-upgrade: ## Applique les migrations de base de données
	docker compose exec api alembic upgrade head

migration-current: ## Affiche la révision actuelle de la base de données
	docker compose exec api alembic current

migration-history: ## Affiche l'historique détaillé des migrations
	docker compose exec api alembic history --verbose

test: install ## Lance les tests avec pytest
	uv run pytest -v -s --cov=api --cov=listener --cov=src  --cov-report=term-missing 

test-specific: install ## Lance un test (ex: make test-specific FILE=tests/api/repositories/test_task_repository.py)
	uv run pytest -v $(FILE)

coverage: ## Lance les tests avec couverture de code
	uv run coverage run -m pytest
	uv run coverage report
	uv run coverage html

clean: ## Nettoyage du dépôt
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

restart-api: ## Redémarre uniquement l'API
	docker compose restart api

restart-listener: ## Redémarre uniquement le listener
	docker compose restart listener

restart-consumer: ## Redémarre uniquement le consumer JS
	docker compose restart consumer

exec-api: ## Ouvre un shell dans le conteneur API
	docker compose exec api bash

exec-db: ## Ouvre un shell dans le conteneur PostgreSQL
	docker compose exec db psql -U postgres -d tasks

info: ## Ouvre l'interface web de RabbitMQ
	@echo "Interface RabbitMQ disponible sur: http://localhost:15672"
	@echo "Login: kalo / Password: kalo"
	@echo "Documentation API disponible sur: http://localhost:8000/docs"

health-check: ## Vérifie la santé des services
	@echo "Vérification de l'API..."
	@curl -s http://localhost:8000/health > /dev/null && echo "✅ API OK" || echo "❌ API KO"
	@echo "Vérification de RabbitMQ..."
	@curl -s http://localhost:15672 > /dev/null && echo "✅ RabbitMQ OK" || echo "❌ RabbitMQ KO"
	@echo "Vérification de la base de données..."
	@docker compose exec db pg_isready -U postgres > /dev/null && echo "✅ DB OK" || echo "❌ DB KO"