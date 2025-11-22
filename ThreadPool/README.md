# ThreadPool - High-Performance Task Scheduler

A header-only C++20 thread pool implementation with work-stealing capabilities, designed for maximum performance and ease of use.

## Features
- Lock-free work queue using std::atomic
- Work-stealing algorithm for load balancing
- Support for futures and promises
- Coroutine support (C++20)
- Zero-copy task submission
- Dynamic thread scaling based on workload

## Usage

### Basic Example
```cpp
#include "ThreadPool.hpp"
using namespace tp;

// Create a thread pool with 4 worker threads
ThreadPool pool(4);

// Enqueue a task and get a future
auto future = pool.enqueue([](int x) { return x * 2; }, 42);
std::cout << future.get() << std::endl; // 84
```

### Multiple Tasks
```cpp
std::vector<std::future<int>> results;

for (int i = 0; i < 10; ++i) {
    results.emplace_back(
        pool.enqueue([](int x) { return x * x; }, i)
    );
}

for (auto& future : results) {
    std::cout << future.get() << std::endl;
}
```

### Parallel Computation
```cpp
// Divide work into chunks for parallel processing
std::vector<int> data(1000000);
size_t chunk_size = data.size() / pool.thread_count();

std::vector<std::future<long long>> partial_sums;
for (size_t i = 0; i < pool.thread_count(); ++i) {
    size_t start = i * chunk_size;
    size_t end = (i == pool.thread_count() - 1) ? data.size() : (i + 1) * chunk_size;

    partial_sums.emplace_back(
        pool.enqueue([&data, start, end]() {
            return std::accumulate(data.begin() + start, data.begin() + end, 0LL);
        })
    );
}

long long total = 0;
for (auto& future : partial_sums) {
    total += future.get();
}
```

## API Reference

### Constructor
- `ThreadPool(size_t num_threads = std::thread::hardware_concurrency())`
  - Creates a thread pool with the specified number of worker threads
  - Defaults to hardware concurrency if not specified

### Methods
- `auto enqueue(F&& f, Args&&... args) -> std::future<return_type>`
  - Enqueues a task for execution
  - Returns a future that will contain the result
  - Thread-safe

- `size_t thread_count() const`
  - Returns the number of worker threads

- `size_t active_tasks() const`
  - Returns the number of currently executing tasks

- `void wait()`
  - Blocks until all queued tasks are complete

## Building

### As Header-Only Library
Simply include `ThreadPool.hpp` in your project:

```cpp
#include "ThreadPool.hpp"
```

### With CMake
```bash
cd ThreadPool
mkdir build && cd build
cmake ..
cmake --build .
./threadpool_example
```

## Performance

The work-stealing algorithm ensures optimal load balancing across threads:
- Threads first try to execute tasks from their own queue (cache-friendly)
- Idle threads steal work from busy threads (load balancing)
- Lock-free operations for minimal contention

## Requirements
- C++20 compatible compiler
- Standard library with `<thread>`, `<future>`, `<atomic>` support
