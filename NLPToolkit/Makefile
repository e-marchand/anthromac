.PHONY: help install install-models test lint format clean docker-build docker-run download-models

help:
	@echo "Available commands:"
	@echo "  install         Install dependencies"
	@echo "  install-models  Download NLP models"
	@echo "  test           Run tests"
	@echo "  lint           Run linting"
	@echo "  format         Format code"
	@echo "  clean          Clean artifacts"
	@echo "  docker-build   Build Docker image"
	@echo "  docker-run     Run Docker container"
	@echo "  download-models Download pre-trained models"
	@echo "  api            Start API server"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-models:
	python -m spacy download en_core_web_sm
	python -m spacy download xx_ent_wiki_sm
	python -m nltk.downloader punkt stopwords wordnet

download-models:
	python scripts/download_models.py --models all

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
	docker build -t nlp-toolkit:latest .

docker-run:
	docker run -p 8000:8000 -v $(PWD)/data:/app/data nlp-toolkit:latest

api:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

notebook:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
