.PHONY: help install test lint format clean docker-build docker-run train evaluate export

help:
	@echo "Available commands:"
	@echo "  install       Install dependencies"
	@echo "  test          Run tests"
	@echo "  lint          Run linting"
	@echo "  format        Format code"
	@echo "  clean         Clean artifacts"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-run    Run Docker container"
	@echo "  train         Train model"
	@echo "  evaluate      Evaluate model"
	@echo "  export        Export model to ONNX/TensorRT"
	@echo "  api           Start API server"
	@echo "  demo          Run webcam demo"

install:
	pip install --upgrade pip
	pip install -r requirements.txt

install-gpu:
	pip install --upgrade pip
	pip install -r requirements-gpu.txt

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
	rm -rf runs/ wandb/

docker-build:
	docker build -t cv-pipeline:latest .

docker-run:
	docker run --gpus all -p 8000:8000 \
	  -v $(PWD)/data:/app/data \
	  -v $(PWD)/models:/app/models \
	  cv-pipeline:latest

train:
	python scripts/train.py --config configs/config.yaml

evaluate:
	python scripts/evaluate.py --config configs/config.yaml

export:
	python scripts/export.py --format onnx
	python scripts/export.py --format tensorrt

api:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

demo:
	python scripts/webcam_demo.py

benchmark:
	python scripts/benchmark.py

notebook:
	jupyter lab --ip=0.0.0.0 --port=8888 --no-browser

download-coco:
	bash scripts/download_coco.sh

download-models:
	python scripts/download_models.py
