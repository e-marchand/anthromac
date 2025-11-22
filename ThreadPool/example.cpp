#include "ThreadPool.hpp"
#include <iostream>
#include <chrono>
#include <numeric>

using namespace tp;

int main() {
    std::cout << "=== ThreadPool Example ===" << std::endl;
    std::cout << "Hardware concurrency: " << std::thread::hardware_concurrency() << std::endl;

    // Example 1: Basic usage
    {
        std::cout << "\n1. Basic usage:" << std::endl;
        ThreadPool pool(4);

        auto future = pool.enqueue([](int x) { return x * 2; }, 42);
        std::cout << "Result: " << future.get() << std::endl; // 84
    }

    // Example 2: Multiple tasks
    {
        std::cout << "\n2. Multiple tasks:" << std::endl;
        ThreadPool pool(4);

        std::vector<std::future<int>> results;

        for (int i = 0; i < 10; ++i) {
            results.emplace_back(
                pool.enqueue([](int x) {
                    std::this_thread::sleep_for(std::chrono::milliseconds(100));
                    return x * x;
                }, i)
            );
        }

        for (size_t i = 0; i < results.size(); ++i) {
            std::cout << "Task " << i << ": " << results[i].get() << std::endl;
        }
    }

    // Example 3: Work-stealing demonstration
    {
        std::cout << "\n3. Work-stealing demonstration:" << std::endl;
        ThreadPool pool(4);

        std::atomic<int> counter{0};
        std::vector<std::future<void>> futures;

        auto start = std::chrono::high_resolution_clock::now();

        // Submit many tasks
        for (int i = 0; i < 100; ++i) {
            futures.emplace_back(
                pool.enqueue([&counter, i]() {
                    counter++;
                    // Simulate variable workload
                    std::this_thread::sleep_for(
                        std::chrono::milliseconds(i % 10)
                    );
                })
            );
        }

        // Wait for all tasks
        for (auto& future : futures) {
            future.get();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << "Completed " << counter << " tasks in "
                  << duration.count() << "ms" << std::endl;
    }

    // Example 4: Parallel computation
    {
        std::cout << "\n4. Parallel sum computation:" << std::endl;
        ThreadPool pool(4);

        std::vector<int> data(1000000);
        std::iota(data.begin(), data.end(), 1);

        auto start = std::chrono::high_resolution_clock::now();

        // Divide work into chunks
        size_t chunk_size = data.size() / pool.thread_count();
        std::vector<std::future<long long>> partial_sums;

        for (size_t i = 0; i < pool.thread_count(); ++i) {
            size_t start_idx = i * chunk_size;
            size_t end_idx = (i == pool.thread_count() - 1)
                ? data.size()
                : (i + 1) * chunk_size;

            partial_sums.emplace_back(
                pool.enqueue([&data, start_idx, end_idx]() {
                    return std::accumulate(
                        data.begin() + start_idx,
                        data.begin() + end_idx,
                        0LL
                    );
                })
            );
        }

        long long total = 0;
        for (auto& future : partial_sums) {
            total += future.get();
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "Parallel sum: " << total << std::endl;
        std::cout << "Time: " << duration.count() << "μs" << std::endl;
    }

    // Example 5: Exception handling
    {
        std::cout << "\n5. Exception handling:" << std::endl;
        ThreadPool pool(2);

        auto future = pool.enqueue([]() {
            throw std::runtime_error("Task error!");
            return 42;
        });

        try {
            future.get();
        } catch (const std::exception& e) {
            std::cout << "Caught exception: " << e.what() << std::endl;
        }
    }

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
