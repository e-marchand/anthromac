# CausalInference - Treatment Effect Estimation

Implementation of cutting-edge causal inference methods for estimating treatment effects from observational data.

## 🎯 Features

### Methods Implemented

#### Matching Methods
- **Propensity Score Matching**: Nearest neighbor, caliper matching
- **Mahalanobis Distance Matching**: Multivariate matching
- **Coarsened Exact Matching (CEM)**: Balance via coarsening

#### Meta-Learners
- **S-Learner**: Single model approach
- **T-Learner**: Two separate models
- **X-Learner**: Cross-fitted meta-learner
- **R-Learner**: Robinson decomposition

#### Tree-Based Methods
- **Causal Forest**: Generalization of random forests for CATE
- **BART**: Bayesian Additive Regression Trees
- **Uplift Trees**: Direct treatment effect modeling

#### Deep Learning Methods
- **TARNet**: Treatment-Agnostic Representation Network
- **DragonNet**: Targeted regularization for CATE
- **CEVAE**: Causal Effect VAE with latent confounders

### Key Capabilities

- **Heterogeneous Treatment Effects (HTE)**: Estimate varying effects across population
- **Sensitivity Analysis**: Test robustness to unmeasured confounding
- **Synthetic Data Generation**: Benchmarking with known ground truth
- **Policy Learning**: Optimal treatment assignment
- **A/B Test Analysis**: CUPED, variance reduction

## 📦 Installation

```bash
pip install -r requirements.txt
```

## 🚀 Quick Start

### Propensity Score Matching

```python
from src.methods.matching.propensity import PropensityScoreMatcher

# Initialize matcher
matcher = PropensityScoreMatcher(caliper=0.1)

# Fit propensity model
matcher.fit(X, treatment)

# Match treated and control units
matches = matcher.match()

# Estimate ATE
ate = matcher.estimate_ate(y)
print(f"Average Treatment Effect: {ate:.3f}")
```

### Meta-Learner (T-Learner)

```python
from src.methods.meta_learners.t_learner import TLearner

# Initialize T-learner
tlearner = TLearner(
    model_t=RandomForestRegressor(),
    model_c=RandomForestRegressor()
)

# Fit on observational data
tlearner.fit(X, treatment, y)

# Estimate CATE for new observations
cate = tlearner.predict_cate(X_test)

# Average Treatment Effect
ate = cate.mean()
```

### Causal Forest

```python
from src.methods.tree_based.causal_forest import CausalForest

# Initialize forest
forest = CausalForest(
    n_estimators=100,
    min_samples_leaf=5
)

# Fit on data
forest.fit(X, treatment, y)

# Predict individual treatment effects
ite = forest.predict(X_test)

# Variable importance for heterogeneity
importance = forest.feature_importances_
```

### Synthetic Data Generation

```python
from src.data.synthetic import SyntheticDataGenerator

# Generate data with known treatment effect
generator = SyntheticDataGenerator(
    n_samples=1000,
    n_features=10,
    treatment_effect=2.0,
    confounding_strength=0.5
)

X, treatment, y, true_cate = generator.generate()

# Validate methods against ground truth
```

## 🏗️ Architecture

```
CausalInference/
├── src/
│   ├── methods/
│   │   ├── matching/           # Matching estimators
│   │   ├── meta_learners/      # Meta-learner approaches
│   │   ├── tree_based/         # Causal forests, BART
│   │   └── deep_learning/      # Neural network methods
│   ├── data/                   # Data generation & loading
│   └── evaluation/            # Validation & metrics
├── notebooks/                 # Example notebooks
└── tests/                    # Unit tests
```

## 📊 Evaluation Metrics

### When Ground Truth Available
- **PEHE**: Precision in Estimation of HTE
- **ATE Error**: Bias in average treatment effect
- **Coverage**: Confidence interval coverage

### Observational Data
- **Balance Checks**: Standardized mean differences
- **Overlap**: Common support diagnostics
- **Placebo Tests**: Negative control outcomes
- **Sensitivity Analysis**: Rosenbaum bounds

## 🧪 Example: Complete Analysis

```python
# 1. Generate synthetic data
from src.data.synthetic import SyntheticDataGenerator

gen = SyntheticDataGenerator(treatment_effect=3.0)
X, treatment, y, true_cate = gen.generate()

# 2. Check balance
from src.evaluation.balance import check_balance

balance = check_balance(X, treatment)
print(f"SMD before matching: {balance['smd'].max():.3f}")

# 3. Propensity score matching
from src.methods.matching.propensity import PropensityScoreMatcher

matcher = PropensityScoreMatcher()
matcher.fit(X, treatment)
X_matched, t_matched, y_matched = matcher.get_matched_data(X, treatment, y)

# 4. Estimate treatment effect
ate_matched = matcher.estimate_ate(y_matched, t_matched)

# 5. CATE estimation with meta-learner
from src.methods.meta_learners.x_learner import XLearner

xlearner = XLearner()
xlearner.fit(X, treatment, y)
cate_pred = xlearner.predict_cate(X)

# 6. Evaluate against ground truth
from src.evaluation.metrics import calculate_pehe

pehe = calculate_pehe(cate_pred, true_cate)
print(f"PEHE: {pehe:.3f}")

# 7. Sensitivity analysis
from src.evaluation.sensitivity import sensitivity_analysis

bounds = sensitivity_analysis(X, treatment, y, gamma_values=[1.0, 1.5, 2.0])
```

## 📈 Visualization

```python
from src.evaluation.plots import plot_cate_distribution

# Plot distribution of treatment effects
plot_cate_distribution(cate_pred, true_cate)

# Plot balance before/after matching
from src.evaluation.plots import plot_balance

plot_balance(X, treatment, X_matched, t_matched)
```

## 🔬 Advanced Features

### Instrumental Variables (IV)

```python
from src.methods.iv.two_stage_least_squares import TwoStageLeastSquares

tsls = TwoStageLeastSquares()
tsls.fit(X, treatment, y, instrument=Z)
late = tsls.estimate_late()  # Local Average Treatment Effect
```

### Regression Discontinuity Design (RDD)

```python
from src.methods.rdd.sharp_rdd import SharpRDD

rdd = SharpRDD(cutoff=0.5, bandwidth=0.1)
rdd.fit(running_variable, y, treatment)
ate_rdd = rdd.estimate_ate()
```

### Difference-in-Differences (DiD)

```python
from src.methods.did.difference_in_differences import DifferenceInDifferences

did = DifferenceInDifferences()
did.fit(panel_data, treated_units, pre_period, post_period)
att = did.estimate_att()  # Average Treatment Effect on Treated
```

## 🤝 Best Practices

1. **Check Assumptions**: Overlap, no unmeasured confounding
2. **Balance Diagnostics**: Verify covariate balance
3. **Sensitivity Analysis**: Test robustness
4. **Cross-Validation**: For CATE estimation
5. **Multiple Methods**: Triangulate results

## 📚 References

- Athey & Imbens (2016): Recursive Partitioning for HTE
- Künzel et al. (2019): Meta-learners for CATE
- Shi et al. (2019): Adapting Neural Networks for Treatment Effects
- Rosenbaum (2002): Sensitivity to Hidden Bias

## 📄 License

MIT License
