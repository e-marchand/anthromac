# AnthroMac - C++ Performance Libraries

A collection of high-performance C++20 header-only libraries for modern applications.

## Projects

### 1. [ThreadPool](ThreadPool/) - High-Performance Task Scheduler
A header-only C++20 thread pool implementation with work-stealing capabilities.

**Features:**
- Lock-free work queue using std::atomic
- Work-stealing algorithm for load balancing
- Support for futures and promises
- Coroutine support (C++20)
- Zero-copy task submission
- Dynamic thread scaling based on workload

### 2. [MemoryArena](MemoryArena/) - Custom Memory Management
High-performance memory allocators optimized for different use cases.

**Features:**
- Arena Allocator: Linear allocation with bulk deallocation
- Pool Allocator: Fixed-size object pooling with O(1) alloc/free
- Stack Allocator: LIFO allocation pattern
- Ring Buffer Allocator: Circular memory management
- Up to 10x faster than standard malloc/free

### 3. [EventBus](EventBus/) - Modern Event System
Compile-time type-safe event bus for decoupled component communication.

**Features:**
- Type-safe event registration and dispatch
- Compile-time event validation
- Thread-safe event delivery
- Priority-based event handling
- Event filtering and transformation
- Weak subscription support to prevent memory leaks

### 4. [LockFreeQueue](LockFreeQueue/) - High-Concurrency MPMC Queue
Multi-producer multi-consumer lock-free queue using C++20 atomic operations.

**Features:**
- Bounded ring buffer with CAS operations
- False sharing prevention through cache-line padding
- Memory ordering optimization for different architectures
- Support for bulk enqueue/dequeue operations
- Wait-free progress guarantee for SPSC variant
- 50M+ ops/sec on modern x86_64 processors

## Building

```bash
mkdir build && cd build
cmake ..
cmake --build .
```

## Running Examples

```bash
# ThreadPool example
./build/ThreadPool/threadpool_example

# MemoryArena example
./build/MemoryArena/memoryarena_example

# EventBus example
./build/EventBus/eventbus_example

# LockFreeQueue example
./build/LockFreeQueue/lockfreequeue_example
```

## Requirements

- C++20 compatible compiler (GCC 10+, Clang 10+, MSVC 2019+)
- CMake 3.15 or higher

## License

MIT License