# EventBus - Modern C++ Event System

A compile-time type-safe event bus implementation using C++17/20 features, perfect for decoupled communication between components.

## Key Features
- Type-safe event registration and dispatch
- Compile-time event validation
- Thread-safe event delivery
- Priority-based event handling
- Event filtering and transformation
- Weak subscription support to prevent memory leaks

## Example
```cpp
EventBus bus;
bus.subscribe<MouseEvent>([](const MouseEvent& e) {
    std::cout << "Mouse: " << e.x << ", " << e.y << std::endl;
});
bus.publish(MouseEvent{100, 200});
```

## Usage

### Basic Event Publishing and Subscribing
```cpp
#include "EventBus.hpp"
using namespace events;

// Define custom events
struct MouseEvent {
    int x, y;
    int button;
};

struct KeyEvent {
    int key;
    bool pressed;
};

// Create event bus
EventBus bus;

// Subscribe to events
auto handle = bus.subscribe<MouseEvent>([](const MouseEvent& e) {
    std::cout << "Mouse clicked at (" << e.x << ", " << e.y << ")" << std::endl;
});

// Publish events
bus.publish(MouseEvent{100, 200, 1});
```

### Priority-Based Handling
```cpp
// Higher priority handlers are called first
bus.subscribe<KeyEvent>([](const KeyEvent& e) {
    std::cout << "High priority handler" << std::endl;
}, EventPriority::High);

bus.subscribe<KeyEvent>([](const KeyEvent& e) {
    std::cout << "Normal priority handler" << std::endl;
}, EventPriority::Normal);
```

### Unsubscribing
```cpp
// Manual unsubscribe
auto handle = bus.subscribe<MouseEvent>([](const MouseEvent& e) {
    // Handle event
});

bus.unsubscribe<MouseEvent>(handle);

// Or use RAII-style scoped subscription
{
    auto scoped = bus.subscribe_scoped<MouseEvent>([](const MouseEvent& e) {
        // Handle event
    });
    // Automatically unsubscribes when scoped goes out of scope
}
```

### Event Filtering
```cpp
// Only handle events that match a predicate
bus.subscribe<MouseEvent>([](const MouseEvent& e) {
    std::cout << "Left button clicked" << std::endl;
}, EventPriority::Normal, [](const MouseEvent& e) {
    return e.button == 1; // Only left button clicks
});
```

## API Reference

### EventBus

**Methods:**
- `template<typename Event> SubscriptionHandle subscribe(Callback<Event> callback, EventPriority priority = EventPriority::Normal)`
  - Subscribe to an event type with optional priority
  - Returns a handle that can be used to unsubscribe

- `template<typename Event> SubscriptionHandle subscribe(Callback<Event> callback, EventPriority priority, Filter<Event> filter)`
  - Subscribe with a filter predicate
  - Only events matching the filter will be delivered

- `template<typename Event> ScopedSubscription subscribe_scoped(Callback<Event> callback, EventPriority priority = EventPriority::Normal)`
  - Subscribe with RAII-style automatic unsubscription
  - Unsubscribes when the returned object is destroyed

- `template<typename Event> void publish(const Event& event)`
  - Publish an event to all subscribers
  - Thread-safe

- `template<typename Event> void publish_async(const Event& event)`
  - Asynchronously publish an event
  - Returns immediately, event delivered on background thread

- `template<typename Event> void unsubscribe(SubscriptionHandle handle)`
  - Manually unsubscribe a handler

- `void clear()`
  - Remove all subscriptions

### EventPriority

Enum values:
- `EventPriority::Low` - Low priority handlers (called last)
- `EventPriority::Normal` - Normal priority (default)
- `EventPriority::High` - High priority handlers (called first)

## Building

### As Header-Only Library
Simply include `EventBus.hpp` in your project:

```cpp
#include "EventBus.hpp"
```

### With CMake
```bash
cd EventBus
mkdir build && cd build
cmake ..
cmake --build .
./eventbus_example
```

## Design Patterns

The EventBus is useful for:
- **Decoupling**: Components don't need to know about each other
- **Observer Pattern**: Multiple listeners for the same event
- **Game Engines**: Input events, collision events, game state changes
- **GUI Systems**: User input, window events, application events
- **Plugin Systems**: Communication between plugins

## Thread Safety

The EventBus is thread-safe:
- Multiple threads can publish events concurrently
- Subscriptions/unsubscriptions are protected
- Async event publishing uses a thread pool

## Requirements
- C++17 compatible compiler (C++20 for some advanced features)
- Standard library with `<functional>`, `<memory>`, `<mutex>` support
