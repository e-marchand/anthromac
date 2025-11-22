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
```cpp
ThreadPool pool(4);
auto future = pool.enqueue([](int x) { return x * 2; }, 42);
std::cout << future.get() << std::endl; // 84
```
