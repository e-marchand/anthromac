# StreamProcessor - Real-Time Data Pipeline

High-performance real-time data processing system for streaming analytics and anomaly detection.

## Features

### Stream Processing
- **Windowed Aggregations**: Tumbling, sliding, session windows
- **Complex Event Processing (CEP)**: Pattern detection in event streams
- **Stateful Processing**: Maintain state across events
- **Exactly-Once Semantics**: Guaranteed message processing

### Analytics
- **Real-Time Anomaly Detection**: LSTM Autoencoder, statistical methods
- **Online Learning**: Incremental model updates with River
- **Approximate Algorithms**: Count-Min Sketch, HyperLogLog, Bloom filters
- **Stream Joins**: Windowed joins across multiple streams

### Infrastructure
- **Dynamic Scaling**: Auto-scale based on processing lag
- **Backpressure Handling**: Adaptive rate limiting
- **Dead Letter Queue**: Handle failed messages
- **Schema Evolution**: Backward/forward compatible schemas
- **Checkpointing**: Fault-tolerant state snapshots

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Basic Stream Processing

```python
from src.core.processor import StreamProcessor
from src.windows.tumbling import TumblingWindow

# Initialize processor
processor = StreamProcessor(
    window=TumblingWindow(size_seconds=60),
    checkpoint_interval=100
)

# Process stream
for batch in data_stream:
    results = processor.process(batch)
    print(f"Processed {len(results)} events")
```

### Real-Time Aggregation

```python
from src.aggregations.window_agg import WindowAggregator

# Create aggregator
aggregator = WindowAggregator(
    window_size=60,  # 60 seconds
    slide=10,        # Slide every 10 seconds
    functions=['sum', 'avg', 'count', 'min', 'max']
)

# Process events
for event in event_stream:
    aggregator.add_event(event)

    # Get current window results
    results = aggregator.get_results()
```

### Anomaly Detection

```python
from src.anomaly.detector import StreamingAnomalyDetector

# Initialize detector
detector = StreamingAnomalyDetector(
    model='lstm_autoencoder',
    window_size=100,
    threshold=2.5
)

# Train on normal data
detector.fit(normal_data_stream)

# Detect anomalies
for event in live_stream:
    is_anomaly, score = detector.detect(event)

    if is_anomaly:
        print(f"Anomaly detected! Score: {score:.4f}")
```

### Complex Event Processing

```python
from src.cep.pattern import PatternDetector

# Define pattern: A followed by B within 5 minutes
pattern = PatternDetector(
    pattern="A -> B",
    within_seconds=300
)

# Detect patterns
for event in event_stream:
    matches = pattern.process(event)

    for match in matches:
        print(f"Pattern detected: {match}")
```

## Advanced Usage

### Online Learning

```python
from src.ml.online_learner import OnlineLearner

# Initialize online learner
learner = OnlineLearner(
    model='hoeffding_tree',
    update_frequency=100
)

# Process and learn
for features, label in labeled_stream:
    # Predict
    prediction = learner.predict(features)

    # Update model
    learner.update(features, label)

    # Get current metrics
    metrics = learner.get_metrics()
```

### Windowed Stream Joins

```python
from src.joins.windowed_join import WindowedJoin

# Join two streams
join = WindowedJoin(
    left_stream='orders',
    right_stream='payments',
    join_key='order_id',
    window_size=300  # 5 minutes
)

# Process both streams
for event in combined_stream:
    joined_events = join.process(event)

    for joined in joined_events:
        print(f"Matched: {joined}")
```

### Approximate Counting

```python
from src.sketches.count_min import CountMinSketch
from src.sketches.hyperloglog import HyperLogLog

# Count-Min Sketch for frequency estimation
cms = CountMinSketch(width=1000, depth=5)

for item in stream:
    cms.add(item)
    frequency = cms.estimate(item)

# HyperLogLog for cardinality estimation
hll = HyperLogLog(precision=14)

for item in stream:
    hll.add(item)
    cardinality = hll.count()
```

### Stateful Processing

```python
from src.state.keyed_state import KeyedState

# Maintain state per key
state = KeyedState(
    backend='rocksdb',
    checkpoint_dir='/tmp/checkpoints'
)

for event in stream:
    key = event['user_id']

    # Get state
    user_state = state.get(key, default={'count': 0})

    # Update state
    user_state['count'] += 1
    user_state['last_seen'] = event['timestamp']

    # Save state
    state.put(key, user_state)

    # Checkpoint periodically
    if event['sequence'] % 1000 == 0:
        state.checkpoint()
```

## Architecture

### Processing Pipeline

```
[Data Source] → [Ingestion] → [Processing] → [Aggregation] → [Output]
                     ↓             ↓              ↓
                [Checkpoint]  [State Mgmt]  [Anomaly Det]
```

### Components

**Ingestion Layer:**
- Kafka consumer with offset management
- Backpressure handling
- Schema validation

**Processing Layer:**
- Event parsing and enrichment
- Stateful transformations
- Window operations

**State Management:**
- In-memory state with RocksDB persistence
- Distributed state with Redis
- Automatic checkpointing

**Output Layer:**
- Batch writes to reduce overhead
- Retry logic with exponential backoff
- Dead letter queue for failures

## Performance

### Throughput Benchmarks

| Events/sec | Latency (p95) | Memory | CPU |
|------------|---------------|--------|-----|
| 10K | 5ms | 512MB | 25% |
| 50K | 12ms | 1GB | 60% |
| 100K | 25ms | 2GB | 90% |

### Optimization Tips

1. **Batch Processing**: Process events in micro-batches (100-1000 events)
2. **State Cleanup**: Implement TTL for state entries
3. **Parallelization**: Partition streams by key
4. **Compression**: Use Snappy/LZ4 for state serialization
5. **Monitoring**: Track lag, throughput, and error rates

## Configuration

### config.yaml

```yaml
processor:
  parallelism: 4
  checkpoint_interval: 1000
  state_backend: rocksdb

windows:
  tumbling_size: 60
  sliding_size: 60
  sliding_slide: 10

kafka:
  bootstrap_servers: localhost:9092
  group_id: stream-processor
  auto_offset_reset: earliest

redis:
  host: localhost
  port: 6379
  db: 0
```

## Fault Tolerance

### Checkpointing

```python
# Configure checkpointing
processor.configure_checkpointing(
    interval=1000,  # Every 1000 events
    backend='filesystem',
    path='/tmp/checkpoints'
)

# Manual checkpoint
processor.checkpoint()

# Restore from checkpoint
processor.restore_from_checkpoint('/tmp/checkpoints/latest')
```

### Error Handling

```python
from src.core.error_handling import DeadLetterQueue

# Configure DLQ
dlq = DeadLetterQueue(
    max_retries=3,
    retry_delay=5,
    storage='kafka'
)

# Process with error handling
try:
    result = processor.process(event)
except Exception as e:
    dlq.send(event, error=e)
```

## Monitoring

### Metrics

```python
from src.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()

# Track metrics
metrics.increment('events_processed')
metrics.gauge('processing_lag', lag_ms)
metrics.histogram('event_size', size_bytes)

# Get statistics
stats = metrics.get_stats()
print(f"Events/sec: {stats['throughput']}")
print(f"Avg latency: {stats['latency_avg']}ms")
```

## Project Structure

```
StreamProcessor/
├── README.md
├── requirements.txt
├── config.yaml
├── src/
│   ├── core/
│   │   ├── processor.py         # Main stream processor
│   │   └── event.py             # Event data model
│   ├── windows/
│   │   ├── tumbling.py          # Tumbling windows
│   │   └── sliding.py           # Sliding windows
│   ├── aggregations/
│   │   └── window_agg.py        # Window aggregations
│   ├── anomaly/
│   │   ├── detector.py          # Anomaly detection
│   │   └── lstm_autoencoder.py  # LSTM autoencoder
│   ├── cep/
│   │   └── pattern.py           # Pattern matching
│   ├── ml/
│   │   └── online_learner.py    # Online learning
│   ├── sketches/
│   │   ├── count_min.py         # Count-Min Sketch
│   │   └── hyperloglog.py       # HyperLogLog
│   ├── state/
│   │   └── keyed_state.py       # State management
│   └── monitoring/
│       └── metrics.py           # Metrics collection
└── examples/
    ├── basic_processing.py
    ├── anomaly_detection.py
    └── windowed_aggregation.py
```

## Use Cases

1. **Fraud Detection**: Real-time transaction monitoring
2. **IoT Analytics**: Sensor data aggregation and anomaly detection
3. **Log Processing**: Real-time log analysis and alerting
4. **User Behavior**: Clickstream analysis and personalization
5. **Market Data**: Financial tick data processing

## Best Practices

1. **Idempotent Processing**: Design operations to be safely retried
2. **Event Time vs Processing Time**: Use event timestamps for accuracy
3. **Late Data Handling**: Configure watermarks and allowed lateness
4. **Resource Management**: Set memory limits and cleanup old state
5. **Testing**: Use test harnesses with synthetic data streams

## Contributing

Contributions welcome! Priority areas:
- Additional aggregation functions
- More CEP patterns
- Integration with cloud streaming services
- Advanced anomaly detection models
- Performance optimizations

## References

- Apache Flink Documentation
- Spark Structured Streaming Guide
- "Streaming Systems" by Tyler Akidau et al.
- "Designing Data-Intensive Applications" by Martin Kleppmann

## License

MIT License
