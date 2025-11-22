.PHONY: help install install-dev test lint format clean docker-build docker-run notebook mlflow

help:
	@echo "Available commands:"
	@echo "  install        Install production dependencies"
	@echo "  install-dev    Install development dependencies"
	@echo "  test           Run tests with pytest"
	@echo "  test-cov       Run tests with coverage"
	@echo "  lint           Run linting checks"
	@echo "  format         Format code with black and isort"
	@echo "  clean          Remove build artifacts and cache"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run Docker container"
	@echo "  notebook       Start Jupyter Lab"
	@echo "  mlflow         Start MLflow UI"
	@echo "  api            Start FastAPI development server"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pre-commit install

test:
	pytest tests/ -v

test-cov:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

lint:
	flake8 src/ tests/ api/
	mypy src/ --ignore-missing-imports
	black --check src/ tests/ api/
	isort --check-only src/ tests/ api/

format:
	black src/ tests/ api/
	isort src/ tests/ api/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage

docker-build:
	docker build -t time-series-forecaster:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/data:/app/data time-series-forecaster:latest

notebook:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root

mlflow:
	mlflow ui --host 0.0.0.0 --port 5000

api:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

# DVC commands
dvc-init:
	dvc init

dvc-add-data:
	dvc add data/raw/
	git add data/raw.dvc .gitignore

dvc-push:
	dvc push

dvc-pull:
	dvc pull

# Training commands
train:
	python -m src.models.forecaster

# Code quality checks
quality: format lint test

# Full setup
setup: install-dev dvc-init
	@echo "Setup complete! Run 'make help' for available commands."
