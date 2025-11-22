# DataQualityEngine - Automated Data Profiling

Automated system for comprehensive data profiling, quality assessment, anomaly detection, and data remediation.

## 🎯 Features

### Data Profiling
- **Statistical Analysis**: Mean, median, std, quartiles, skewness, kurtosis
- **Distribution Detection**: Automatic distribution fitting (normal, exponential, uniform)
- **Type Inference**: Intelligent data type detection beyond pandas dtypes
- **Cardinality Analysis**: Unique values, duplicates, most frequent values

### Quality Assessment
- **Completeness**: Missing value analysis with patterns
- **Validity**: Range checks, format validation, business rules
- **Consistency**: Cross-column consistency checks
- **Accuracy**: Statistical outlier detection
- **Quality Score**: Weighted composite score (0-100)

### Anomaly Detection
- **Isolation Forest**: Tree-based anomaly detection
- **Local Outlier Factor (LOF)**: Density-based outliers
- **Statistical Methods**: Z-score, IQR, Grubbs' test
- **Time Series Anomalies**: Seasonal decomposition

### Data Drift Detection
- **Population Stability Index (PSI)**: Detect distribution shifts
- **Kolmogorov-Smirnov Test**: Statistical drift testing
- **Chi-Square Test**: Categorical drift detection
- **Jensen-Shannon Divergence**: Distribution similarity

### Data Remediation
- **Missing Imputation**: MICE, KNN, Forward fill, Median/Mode
- **Deduplication**: Fuzzy matching with MinHash LSH
- **Standardization**: Automatic formatting and normalization
- **Outlier Handling**: Cap, remove, or transform

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Data Profiling

```python
from src.profiling.profiler import DataProfiler

# Initialize profiler
profiler = DataProfiler()

# Profile dataset
profile = profiler.profile(df)

# View summary
print(f"Total rows: {profile['summary']['n_rows']}")
print(f"Total columns: {profile['summary']['n_columns']}")
print(f"Missing cells: {profile['summary']['missing_cells_pct']:.2f}%")

# Column-level details
for col, stats in profile['columns'].items():
    print(f"\n{col}:")
    print(f"  Type: {stats['type']}")
    print(f"  Missing: {stats['missing_pct']:.2f}%")
    if stats['type'] == 'numeric':
        print(f"  Mean: {stats['mean']:.2f}")
        print(f"  Std: {stats['std']:.2f}")
```

### Anomaly Detection

```python
from src.anomaly.detector import AnomalyDetector

# Initialize detector
detector = AnomalyDetector(method='isolation_forest')

# Fit on data
detector.fit(df)

# Detect anomalies
anomalies = detector.detect(df)

print(f"Found {anomalies.sum()} anomalies ({anomalies.mean()*100:.2f}%)")

# Get anomaly scores
scores = detector.get_scores(df)
```

### Data Drift Detection

```python
from src.quality.drift import DriftDetector

# Initialize drift detector
drift_detector = DriftDetector()

# Set baseline
drift_detector.set_baseline(train_df)

# Check for drift in production data
drift_report = drift_detector.detect_drift(prod_df)

if drift_report['has_drift']:
    print(f"⚠️  Drift detected in {len(drift_report['drifted_columns'])} columns")
    for col in drift_report['drifted_columns']:
        psi = drift_report['drift_scores'][col]['psi']
        print(f"  {col}: PSI = {psi:.4f}")
```

### Quality Scoring

```python
from src.quality.scorer import QualityScorer

# Initialize scorer
scorer = QualityScorer()

# Compute quality score
quality_report = scorer.score(df)

print(f"Overall Quality Score: {quality_report['overall_score']:.1f}/100")
print("\nDimensions:")
print(f"  Completeness: {quality_report['dimensions']['completeness']:.1f}")
print(f"  Validity: {quality_report['dimensions']['validity']:.1f}")
print(f"  Consistency: {quality_report['dimensions']['consistency']:.1f}")
print(f"  Accuracy: {quality_report['dimensions']['accuracy']:.1f}")
```

### Data Imputation

```python
from src.imputation.imputer import SmartImputer

# Initialize imputer
imputer = SmartImputer(strategy='auto')

# Fit and transform
df_imputed = imputer.fit_transform(df)

# Get imputation report
report = imputer.get_imputation_report()
print(f"Imputed {report['total_imputed']} missing values")
```

## 🏗️ Architecture

```
DataQualityEngine/
├── src/
│   ├── profiling/          # Statistical profiling
│   │   └── profiler.py
│   ├── quality/            # Quality assessment
│   │   ├── scorer.py
│   │   └── drift.py
│   ├── anomaly/            # Anomaly detection
│   │   └── detector.py
│   └── imputation/         # Missing data handling
│       └── imputer.py
├── configs/                # Configuration files
├── tests/                  # Unit tests
└── notebooks/             # Example notebooks
```

## 📊 Quality Dimensions

### Completeness (30% weight)
- Missing value percentage
- Column completeness
- Row completeness

### Validity (25% weight)
- Data type conformance
- Range validity
- Format validity
- Business rule compliance

### Consistency (20% weight)
- Referential integrity
- Cross-column consistency
- Temporal consistency

### Accuracy (25% weight)
- Outlier percentage
- Duplicate percentage
- Precision/recall (if ground truth available)

## 🔧 Configuration

```yaml
# configs/quality_config.yaml
quality_thresholds:
  completeness: 0.95
  validity: 0.90
  consistency: 0.85
  accuracy: 0.90

anomaly_detection:
  method: isolation_forest
  contamination: 0.1

drift_detection:
  psi_threshold: 0.1
  ks_threshold: 0.05

imputation:
  strategy: auto
  max_missing_pct: 0.5
```

## 📈 Monitoring Dashboard

Access the quality dashboard at `http://localhost:8050`

Features:
- Real-time quality metrics
- Drift alerts
- Anomaly timeline
- Column-level statistics
- Quality trends over time

## 🚨 Alerting

Configure alerts for:
- Quality score drops below threshold
- Drift detected in critical columns
- Anomaly rate exceeds baseline
- Schema changes detected

Integration with:
- Slack
- PagerDuty
- Email
- Custom webhooks

## 🧪 Example: Complete Pipeline

```python
from src.profiling.profiler import DataProfiler
from src.quality.scorer import QualityScorer
from src.anomaly.detector import AnomalyDetector
from src.quality.drift import DriftDetector
from src.imputation.imputer import SmartImputer

# 1. Profile data
profiler = DataProfiler()
profile = profiler.profile(df)
print(f"Dataset has {profile['summary']['n_rows']} rows")

# 2. Check quality
scorer = QualityScorer()
quality = scorer.score(df)
print(f"Quality score: {quality['overall_score']:.1f}/100")

# 3. Detect anomalies
detector = AnomalyDetector()
detector.fit(df)
anomalies = detector.detect(df)
df_clean = df[~anomalies]

# 4. Check for drift
drift_detector = DriftDetector()
drift_detector.set_baseline(historical_df)
drift = drift_detector.detect_drift(df)

if drift['has_drift']:
    print(f"⚠️  Drift detected!")

# 5. Handle missing values
imputer = SmartImputer()
df_imputed = imputer.fit_transform(df_clean)

# 6. Final quality check
final_quality = scorer.score(df_imputed)
print(f"Final quality: {final_quality['overall_score']:.1f}/100")
```

## 🤝 Best Practices

1. **Establish Baselines**: Profile data in development
2. **Monitor Continuously**: Track quality in production
3. **Alert on Changes**: Configure thresholds
4. **Document Rules**: Maintain quality requirements
5. **Version Profiles**: Track changes over time

## 📚 Use Cases

- **Data Pipeline Validation**: Automated quality gates
- **ML Feature Quality**: Monitor feature drift
- **Regulatory Compliance**: Data quality reporting
- **Data Migration**: Validate transfer accuracy
- **Vendor Data**: Assess external data quality

## 📄 License

MIT License
