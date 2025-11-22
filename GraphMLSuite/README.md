# GraphMLSuite - Graph Neural Network Toolkit

Complete toolkit for graph machine learning with modern GNN architectures.

## Features

### GNN Architectures
- **GCN (Graph Convolutional Network)**: Spectral-based graph convolution
- **GAT (Graph Attention Network)**: Attention-based message passing
- **GraphSAGE**: Inductive graph learning with sampling

### Tasks
- **Node Classification**: Classify nodes in graphs
- **Link Prediction**: Predict missing edges
- **Graph Classification**: Classify entire graphs

### Utilities
- Graph construction and manipulation
- Feature engineering for graphs
- Visualization tools
- Benchmark datasets

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Node Classification with GCN

```python
from src.models.gcn import GCN
from src.data.loader import load_cora

# Load dataset
graph, features, labels, train_mask, test_mask = load_cora()

# Initialize model
model = GCN(
    input_dim=features.shape[1],
    hidden_dim=64,
    output_dim=labels.max() + 1,
    num_layers=2,
    dropout=0.5
)

# Train
model.fit(graph, features, labels, train_mask, epochs=200)

# Evaluate
accuracy = model.evaluate(graph, features, labels, test_mask)
print(f"Test Accuracy: {accuracy:.4f}")
```

### Node Classification with GAT

```python
from src.models.gat import GAT

# Initialize with attention
model = GAT(
    input_dim=features.shape[1],
    hidden_dim=64,
    output_dim=labels.max() + 1,
    num_heads=8,
    dropout=0.6
)

model.fit(graph, features, labels, train_mask)
```

### Graph Classification with GraphSAGE

```python
from src.models.graphsage import GraphSAGE
from src.data.loader import load_graph_dataset

# Load graph dataset
graphs, labels = load_graph_dataset('MUTAG')

# Initialize model
model = GraphSAGE(
    input_dim=graphs[0].num_features,
    hidden_dim=64,
    output_dim=len(set(labels)),
    aggregator='mean'
)

# Train
model.fit(graphs, labels)
```

### Link Prediction

```python
from src.tasks.link_prediction import LinkPredictor

# Initialize predictor
predictor = LinkPredictor(
    input_dim=features.shape[1],
    hidden_dim=64,
    model_type='gcn'
)

# Train
predictor.fit(graph, features)

# Predict
edge_probs = predictor.predict_edges([(0, 1), (5, 10), (3, 7)])
```

## Architecture Details

### GCN (Graph Convolutional Network)

Implements spectral graph convolution:

```
H^(l+1) = σ(D̃^(-1/2) Ã D̃^(-1/2) H^(l) W^(l))
```

- **Input**: Node features, adjacency matrix
- **Output**: Node embeddings
- **Best for**: Transductive learning, homophilic graphs

### GAT (Graph Attention Network)

Uses attention mechanism for neighbor aggregation:

```
h_i' = σ(∑_{j∈N(i)} α_{ij} W h_j)
α_{ij} = softmax(LeakyReLU(a^T [W h_i || W h_j]))
```

- **Input**: Node features, adjacency matrix
- **Output**: Node embeddings with attention weights
- **Best for**: Graphs with varying neighbor importance

### GraphSAGE

Inductive learning with sampling:

```
h_N(v) = AGG({h_u, ∀u ∈ N(v)})
h_v' = σ(W · [h_v || h_N(v)])
```

Aggregators:
- **Mean**: Average of neighbor features
- **Pool**: Max pooling with MLP
- **LSTM**: LSTM aggregation

- **Input**: Node features, adjacency matrix
- **Output**: Node embeddings
- **Best for**: Inductive learning, large graphs

## Dataset Support

### Built-in Datasets

**Citation Networks:**
- Cora: 2708 papers, 7 classes
- Citeseer: 3327 papers, 6 classes
- Pubmed: 19717 papers, 3 classes

**Graph Classification:**
- MUTAG: 188 molecules
- PROTEINS: 1113 proteins
- ENZYMES: 600 proteins

### Custom Graphs

```python
from src.data.graph import Graph

# Create custom graph
edges = [(0, 1), (1, 2), (2, 0)]
features = np.random.randn(3, 10)
labels = [0, 1, 0]

graph = Graph(edges=edges, num_nodes=3)
```

## Advanced Usage

### Custom GNN Layer

```python
from src.models.base import GNNLayer
import torch
import torch.nn as nn

class CustomGNNLayer(GNNLayer):
    def __init__(self, input_dim, output_dim):
        super().__init__()
        self.linear = nn.Linear(input_dim, output_dim)

    def forward(self, x, adj):
        # Custom message passing
        messages = torch.sparse.mm(adj, x)
        return self.linear(messages)
```

### Graph Construction

```python
from src.data.graph_builder import GraphBuilder

# Build k-NN graph from features
builder = GraphBuilder()
graph = builder.build_knn_graph(features, k=5)

# Build similarity graph
graph = builder.build_similarity_graph(
    features,
    threshold=0.5,
    metric='cosine'
)
```

### Feature Engineering

```python
from src.features.graph_features import compute_node_features

# Compute structural features
structural_features = compute_node_features(graph, [
    'degree',
    'clustering_coefficient',
    'pagerank',
    'betweenness'
])

# Combine with existing features
features_combined = np.hstack([features, structural_features])
```

## Benchmarks

Performance on standard datasets:

| Model | Cora | Citeseer | Pubmed |
|-------|------|----------|--------|
| GCN | 81.5% | 70.3% | 79.0% |
| GAT | 83.0% | 72.5% | 79.0% |
| GraphSAGE | 80.1% | 68.9% | 77.2% |

## API Reference

### Models

**GCN**
- `__init__(input_dim, hidden_dim, output_dim, num_layers, dropout)`
- `fit(graph, features, labels, train_mask, epochs, lr)`
- `predict(graph, features)` → predictions
- `evaluate(graph, features, labels, mask)` → accuracy

**GAT**
- `__init__(input_dim, hidden_dim, output_dim, num_heads, dropout)`
- `fit(graph, features, labels, train_mask, epochs, lr)`
- `get_attention_weights()` → attention matrices

**GraphSAGE**
- `__init__(input_dim, hidden_dim, output_dim, aggregator)`
- `fit(graphs, labels, epochs, lr)`
- `predict(graphs)` → predictions

### Data Structures

**Graph**
- `add_edges(edges)`: Add edges
- `get_adjacency()` → sparse adjacency matrix
- `get_neighbors(node)` → list of neighbors
- `num_nodes`: Number of nodes
- `num_edges`: Number of edges

## Project Structure

```
GraphMLSuite/
├── README.md
├── requirements.txt
├── src/
│   ├── models/
│   │   ├── gcn.py              # GCN implementation
│   │   ├── gat.py              # GAT implementation
│   │   └── graphsage.py        # GraphSAGE implementation
│   ├── data/
│   │   ├── loader.py           # Dataset loaders
│   │   ├── graph.py            # Graph data structure
│   │   └── graph_builder.py    # Graph construction
│   ├── tasks/
│   │   ├── node_classification.py
│   │   ├── link_prediction.py
│   │   └── graph_classification.py
│   └── features/
│       └── graph_features.py   # Feature engineering
└── examples/
    ├── node_classification.py
    ├── link_prediction.py
    └── graph_classification.py
```

## Contributing

Contributions welcome! Areas of interest:
- Additional GNN architectures (GIN, PNA, etc.)
- More benchmark datasets
- Distributed training support
- Graph generation models

## References

- Kipf & Welling (2017): "Semi-Supervised Classification with Graph Convolutional Networks"
- Veličković et al. (2018): "Graph Attention Networks"
- Hamilton et al. (2017): "Inductive Representation Learning on Large Graphs"

## License

MIT License
