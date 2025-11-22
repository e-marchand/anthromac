# MLOpsFramework - Automated ML Pipeline

Complete MLOps setup demonstrating best practices for model lifecycle management, from data validation to production deployment.

## 🎯 Features

### Data Validation
- **Schema Validation**: Pandera for DataFrame validation
- **Data Quality**: Automated checks for missing values, outliers
- **Drift Detection**: Statistical tests for distribution shifts

### Feature Engineering
- **Feature Store**: Simple in-memory feature store with versioning
- **Transformations**: Scalers, encoders, feature generation
- **Validation**: Feature schema validation

### Model Training
- **Experiment Tracking**: MLflow integration for metrics and parameters
- **Model Versioning**: Automated model registry
- **Hyperparameter Tuning**: Optuna integration
- **Cross-Validation**: K-fold with stratification

### Model Monitoring
- **Performance Metrics**: Real-time model performance tracking
- **Data Drift**: Distribution comparison (KS test, PSI)
- **Prediction Drift**: Target distribution monitoring
- **Alerting**: Configurable thresholds

### CI/CD Pipeline
- **Automated Testing**: Unit tests, integration tests
- **Model Validation**: Performance gates
- **Deployment**: Blue-green deployments
- **Rollback**: Automatic rollback on performance degradation

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Training Pipeline

```python
from src.pipeline.training.trainer import MLOpsTrainer

# Initialize trainer
trainer = MLOpsTrainer(
    experiment_name="my_experiment",
    tracking_uri="mlruns"
)

# Train model
trainer.train(X_train, y_train, model_type='xgboost')

# Track metrics
trainer.log_metrics({'accuracy': 0.95})

# Save model
trainer.save_model('models/my_model.pkl')
```

### Data Validation

```python
from src.validation.validator import DataValidator

validator = DataValidator()

# Validate schema
validator.validate_schema(df, schema_path='configs/schema.yaml')

# Check data quality
report = validator.quality_check(df)
print(report)
```

### Monitoring

```python
from src.monitoring.monitor import ModelMonitor

monitor = ModelMonitor()

# Check for data drift
drift_report = monitor.detect_drift(
    reference_data=train_df,
    current_data=prod_df
)

# Performance monitoring
monitor.track_predictions(y_true, y_pred)
```

## 🏗️ Architecture

```
MLOpsFramework/
├── src/
│   ├── pipeline/
│   │   ├── data/           # Data loading and preprocessing
│   │   ├── features/       # Feature engineering
│   │   ├── training/       # Model training
│   │   └── deployment/     # Model deployment
│   ├── monitoring/         # Model and data monitoring
│   ├── validation/         # Data validation
│   └── tracking/          # Experiment tracking
├── configs/               # Configuration files
├── tests/                # Unit and integration tests
└── .github/workflows/    # CI/CD pipelines
```

## 📊 Metrics Tracked

### Training Metrics
- Model performance (accuracy, F1, AUC-ROC)
- Training time
- Resource utilization
- Hyperparameters

### Production Metrics
- Inference latency
- Throughput (predictions/sec)
- Data drift scores (KS statistic, PSI)
- Prediction drift
- Error rates

## 🔧 Configuration

All configurations are in YAML format:

```yaml
# configs/training.yaml
model:
  type: xgboost
  params:
    n_estimators: 100
    max_depth: 6

tracking:
  experiment_name: production
  tracking_uri: mlruns

monitoring:
  drift_threshold: 0.1
  performance_threshold: 0.8
```

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run specific test suite
pytest tests/test_pipeline.py

# With coverage
pytest --cov=src tests/
```

## 🚢 Deployment

### Local Deployment
```bash
python src/pipeline/deployment/deploy.py --model models/best_model.pkl
```

### Docker Deployment
```bash
docker build -t mlops-framework .
docker run -p 8000:8000 mlops-framework
```

### Kubernetes
```bash
kubectl apply -f k8s/deployment.yaml
```

## 📈 Monitoring Dashboard

Access the monitoring dashboard at `http://localhost:8000/monitoring`

Features:
- Real-time metrics
- Drift detection alerts
- Model performance trends
- Resource utilization

## 🔄 CI/CD Pipeline

GitHub Actions workflow includes:
1. **Linting**: flake8, black, mypy
2. **Testing**: pytest with coverage
3. **Model Validation**: Performance thresholds
4. **Docker Build**: Containerization
5. **Deployment**: Automated to staging/production

## 📚 Best Practices

1. **Version Everything**: Data, code, models, configurations
2. **Automate Testing**: Unit, integration, and model tests
3. **Monitor Continuously**: Data drift, model performance
4. **Document**: Experiments, decisions, model cards
5. **Rollback Ready**: Always have a previous stable version

## 🤝 Contributing

See CONTRIBUTING.md for guidelines.

## 📄 License

MIT License
