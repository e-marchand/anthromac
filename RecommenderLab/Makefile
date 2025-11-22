.PHONY: help install test lint format clean docker-build docker-up docker-down notebook api

help:
	@echo "Available commands:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linting"
	@echo "  format        Format code"
	@echo "  clean         Clean artifacts"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-up     Start Docker services"
	@echo "  docker-down   Stop Docker services"
	@echo "  notebook      Start Jupyter Lab"
	@echo "  api           Start API server"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

test:
	pytest tests/ -v

lint:
	flake8 src/ tests/ api/
	mypy src/ --ignore-missing-imports

format:
	black src/ tests/ api/
	isort src/ tests/ api/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	rm -rf build/ dist/ *.egg-info

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

notebook:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

api:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000
