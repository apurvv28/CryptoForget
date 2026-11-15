.PHONY: help install dev backend frontend test lint db-up db-down model

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install all dependencies
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

dev: ## Install dev dependencies
	cd backend && pip install -r requirements-dev.txt

backend: ## Start FastAPI dev server
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

frontend: ## Start React dev server
	cd frontend && npm run dev

test: ## Run all tests
	pytest tests/ -v

lint: ## Run linting
	ruff check backend/ ml/ tests/
	mypy backend/ ml/

localstack-up: ## Optional: Start LocalStack S3 for offline testing
	docker-compose --profile offline-test up -d

localstack-down: ## Stop LocalStack
	docker-compose down

model: ## Download and pin DistilGPT2
	python -m ml.scripts.download_model
