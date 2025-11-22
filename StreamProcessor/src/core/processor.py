"""Core stream processor implementation."""

import numpy as np
from typing import List, Dict, Any, Optional, Callable
from collections import deque
import time
import logging

logger = logging.getLogger(__name__)


class Event:
    """Represents a streaming event."""

    def __init__(
        self,
        data: Dict[str, Any],
        timestamp: Optional[float] = None,
        key: Optional[str] = None
    ):
        """
        Initialize event.

        Args:
            data: Event data
            timestamp: Event timestamp (defaults to current time)
            key: Partition key
        """
        self.data = data
        self.timestamp = timestamp if timestamp is not None else time.time()
        self.key = key

    def __repr__(self):
        return f"Event(key={self.key}, timestamp={self.timestamp}, data={self.data})"


class StreamProcessor:
    """
    Core stream processing engine.

    Handles event processing, windowing, and state management.
    """

    def __init__(
        self,
        window_size: int = 60,
        checkpoint_interval: int = 1000,
        max_buffer_size: int = 10000
    ):
        """
        Initialize stream processor.

        Args:
            window_size: Window size in seconds
            checkpoint_interval: Events between checkpoints
            max_buffer_size: Maximum events to buffer
        """
        self.window_size = window_size
        self.checkpoint_interval = checkpoint_interval
        self.max_buffer_size = max_buffer_size

        # State
        self.event_buffer = deque(maxlen=max_buffer_size)
        self.state = {}
        self.event_count = 0
        self.last_checkpoint = 0

        # Metrics
        self.metrics = {
            'events_processed': 0,
            'events_dropped': 0,
            'processing_time_ms': 0,
            'checkpoint_count': 0
        }

        logger.info(f"Initialized StreamProcessor (window={window_size}s, "
                   f"checkpoint_interval={checkpoint_interval})")

    def process(
        self,
        events: List[Event],
        transform_fn: Optional[Callable] = None
    ) -> List[Event]:
        """
        Process a batch of events.

        Args:
            events: List of events to process
            transform_fn: Optional transformation function

        Returns:
            Processed events
        """
        start_time = time.time()

        processed = []

        for event in events:
            # Apply transformation
            if transform_fn is not None:
                try:
                    event = transform_fn(event)
                except Exception as e:
                    logger.error(f"Error transforming event: {e}")
                    self.metrics['events_dropped'] += 1
                    continue

            # Add to buffer
            self.event_buffer.append(event)

            # Update state
            if event.key is not None:
                self._update_state(event)

            processed.append(event)
            self.event_count += 1

            # Checkpoint if needed
            if self.event_count - self.last_checkpoint >= self.checkpoint_interval:
                self.checkpoint()

        # Update metrics
        self.metrics['events_processed'] += len(processed)
        processing_time = (time.time() - start_time) * 1000
        self.metrics['processing_time_ms'] = processing_time

        logger.debug(f"Processed {len(processed)} events in {processing_time:.2f}ms")

        return processed

    def get_window_events(
        self,
        window_start: Optional[float] = None,
        window_end: Optional[float] = None
    ) -> List[Event]:
        """
        Get events in a time window.

        Args:
            window_start: Window start timestamp
            window_end: Window end timestamp

        Returns:
            Events in window
        """
        if window_end is None:
            window_end = time.time()

        if window_start is None:
            window_start = window_end - self.window_size

        events = [
            event for event in self.event_buffer
            if window_start <= event.timestamp < window_end
        ]

        return events

    def aggregate(
        self,
        field: str,
        function: str = 'sum',
        window_start: Optional[float] = None,
        window_end: Optional[float] = None
    ) -> float:
        """
        Aggregate events in window.

        Args:
            field: Field to aggregate
            function: Aggregation function ('sum', 'avg', 'min', 'max', 'count')
            window_start: Window start
            window_end: Window end

        Returns:
            Aggregated value
        """
        events = self.get_window_events(window_start, window_end)

        if not events:
            return 0.0

        values = [event.data.get(field, 0) for event in events]

        if function == 'sum':
            return sum(values)
        elif function == 'avg':
            return sum(values) / len(values)
        elif function == 'min':
            return min(values)
        elif function == 'max':
            return max(values)
        elif function == 'count':
            return len(values)
        else:
            raise ValueError(f"Unknown function: {function}")

    def checkpoint(self):
        """Create checkpoint of current state."""
        logger.info(f"Checkpointing at event {self.event_count}")

        # In production, save state to persistent storage
        # For now, just track checkpoint count
        self.metrics['checkpoint_count'] += 1
        self.last_checkpoint = self.event_count

    def get_metrics(self) -> Dict[str, Any]:
        """Get processing metrics."""
        return self.metrics.copy()

    def _update_state(self, event: Event):
        """Update keyed state."""
        if event.key not in self.state:
            self.state[event.key] = {
                'count': 0,
                'last_seen': 0,
                'total': 0
            }

        state = self.state[event.key]
        state['count'] += 1
        state['last_seen'] = event.timestamp

        # Update total if numeric value present
        if 'value' in event.data:
            state['total'] += event.data['value']

    def get_state(self, key: str) -> Optional[Dict[str, Any]]:
        """Get state for key."""
        return self.state.get(key)

    def clear_old_events(self, max_age_seconds: int = 3600):
        """
        Clear events older than max age.

        Args:
            max_age_seconds: Maximum event age in seconds
        """
        cutoff = time.time() - max_age_seconds

        # Remove old events
        while self.event_buffer and self.event_buffer[0].timestamp < cutoff:
            self.event_buffer.popleft()

        logger.debug(f"Cleared old events, {len(self.event_buffer)} remaining")


def main():
    """Example usage."""
    print("=" * 80)
    print("Stream Processor - Example")
    print("=" * 80)

    # Initialize processor
    processor = StreamProcessor(
        window_size=10,  # 10 seconds
        checkpoint_interval=100
    )

    print(f"\nProcessor initialized")
    print(f"  Window size: {processor.window_size}s")
    print(f"  Checkpoint interval: {processor.checkpoint_interval}")

    # Generate sample events
    print("\n[1] Processing events...")

    events = []
    base_time = time.time()

    for i in range(500):
        event = Event(
            data={
                'value': np.random.randint(1, 100),
                'sensor_id': f"sensor_{i % 10}",
                'status': np.random.choice(['ok', 'warning', 'error'])
            },
            timestamp=base_time + i * 0.1,  # Events every 100ms
            key=f"sensor_{i % 10}"
        )
        events.append(event)

    # Process events
    processed = processor.process(events)

    print(f"  Processed: {len(processed)} events")
    print(f"  Buffered: {len(processor.event_buffer)} events")

    # Test aggregations
    print("\n[2] Window aggregations:")

    window_end = base_time + 50
    window_start = window_end - 10

    total = processor.aggregate('value', 'sum', window_start, window_end)
    avg = processor.aggregate('value', 'avg', window_start, window_end)
    count = processor.aggregate('value', 'count', window_start, window_end)

    print(f"  Window: {window_start:.2f} - {window_end:.2f}")
    print(f"  Total: {total:.2f}")
    print(f"  Average: {avg:.2f}")
    print(f"  Count: {count:.0f}")

    # Test state management
    print("\n[3] State management:")

    for i in range(10):
        key = f"sensor_{i}"
        state = processor.get_state(key)
        if state:
            print(f"  {key}: count={state['count']}, total={state['total']:.2f}")

    # Metrics
    print("\n[4] Processing metrics:")
    metrics = processor.get_metrics()

    for metric, value in metrics.items():
        print(f"  {metric}: {value}")

    # Test transformation
    print("\n[5] Event transformation:")

    def enrich_event(event: Event) -> Event:
        """Add enrichment to event."""
        event.data['enriched'] = True
        event.data['processing_time'] = time.time()
        return event

    new_events = [
        Event(
            data={'value': i, 'sensor_id': f"sensor_{i}"},
            key=f"sensor_{i}"
        )
        for i in range(10)
    ]

    enriched = processor.process(new_events, transform_fn=enrich_event)

    print(f"  Processed {len(enriched)} events with enrichment")
    print(f"  Sample enriched event: {enriched[0].data}")

    # Clear old events
    print("\n[6] Cleanup:")
    print(f"  Events before cleanup: {len(processor.event_buffer)}")

    processor.clear_old_events(max_age_seconds=30)

    print(f"  Events after cleanup: {len(processor.event_buffer)}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
