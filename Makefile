.PHONY: help install dev-install test lint format clean setup-db run-dev build

help:  ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install production dependencies
	pip install -r requirements.txt

dev-install:  ## Install development dependencies
	pip install -r requirements.txt
	pre-commit install

test:  ## Run tests
	pytest tests/ -v --cov=src --cov-report=html

lint:  ## Run linting
	black --check src/ tests/
	isort --check-only src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/
	isort src/ tests/

clean:  ## Clean cache and build files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .coverage htmlcov/ .pytest_cache/ build/ dist/ *.egg-info/

setup-db:  ## Setup database
	python -c "from src.services.load import _create_tables, _get_db_connection; conn = _get_db_connection(); _create_tables(conn); conn.close()"

run-dev:  ## Run development server
	python main.py --verbose

run-api:  ## Run API server
	uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

build:  ## Build Docker image
	docker build -t halifax-sentiment:latest .

docker-up:  ## Start Docker services
	docker-compose up -d

docker-down:  ## Stop Docker services
	docker-compose down

docker-logs:  ## View Docker logs
	docker-compose logs -f