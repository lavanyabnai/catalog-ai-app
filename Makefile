.PHONY: install dev test lint db-migrate db-reset db-seed types help

PYTHON = python3
UV = uv
PNPM = pnpm

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies (pnpm + uv)
	@echo "Installing JS dependencies..."
	$(PNPM) install
	@echo "Installing Python API dependencies..."
	cd apps/api && $(UV) sync
	@echo "Installing Python worker dependencies..."
	cd apps/worker && $(UV) sync
	@echo "Copying .env.example to .env if not present..."
	@test -f .env || cp .env.example .env
	@echo "Done! Run 'make dev' to start the dev server."

dev: ## Start all services via Docker Compose
	docker compose up --build

dev-web: ## Start only the Next.js dev server
	$(PNPM) --filter web dev

dev-api: ## Start only the FastAPI dev server
	cd apps/api && $(UV) run uvicorn main:app --reload --host 0.0.0.0 --port 8000

dev-worker: ## Start only the Celery worker
	cd apps/worker && $(UV) run celery -A celery_app worker --loglevel=info

test: ## Run all tests
	@echo "Running Python tests..."
	cd apps/api && $(UV) run pytest -q
	@echo "Running JS type check..."
	$(PNPM) --filter web run build --no-lint || true

lint: ## Run linters
	@echo "Linting Python..."
	cd apps/api && $(UV) run ruff check .
	@echo "Linting Next.js..."
	$(PNPM) --filter web lint

db-migrate: ## Apply Alembic migrations to the database
	cd apps/api && $(UV) run alembic upgrade head

db-reset: ## Drop and recreate the database, then apply all migrations
	cd apps/api && $(UV) run alembic downgrade base && $(UV) run alembic upgrade head

db-seed: ## Seed the database with initial data
	cd apps/api && $(UV) run python -m app.seed

types: ## Generate TypeScript types from the live OpenAPI schema
	$(PYTHON) scripts/gen_types.py
