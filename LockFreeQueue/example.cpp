#include "LockFreeQueue.hpp"
#include <iostream>
#include <thread>
#include <vector>
#include <chrono>
#include <string>
#include <atomic>
#include <numeric>

using namespace lockfree;

// Example 1: Basic SPSC Queue Usage
void example_spsc_basic() {
    std::cout << "\n=== Example 1: Basic SPSC Queue ===" << std::endl;

    SPSCQueue<int> queue(16);

    std::cout << "Queue capacity: " << queue.capacity() << std::endl;

    // Producer thread
    std::thread producer([&queue]() {
        for (int i = 0; i < 10; ++i) {
            while (!queue.enqueue(i)) {
                // Retry if queue is full
                std::this_thread::yield();
            }
            std::cout << "Produced: " << i << std::endl;
        }
    });

    // Consumer thread
    std::thread consumer([&queue]() {
        for (int i = 0; i < 10; ++i) {
            int value;
            while (!queue.dequeue(value)) {
                // Retry if queue is empty
                std::this_thread::yield();
            }
            std::cout << "Consumed: " << value << std::endl;
        }
    });

    producer.join();
    consumer.join();

    std::cout << "Queue size after completion: " << queue.size() << std::endl;
}

// Example 2: Basic MPMC Queue Usage
void example_mpmc_basic() {
    std::cout << "\n=== Example 2: Basic MPMC Queue ===" << std::endl;

    MPMCQueue<std::string> queue(32);

    // Multiple producers
    std::vector<std::thread> producers;
    for (int p = 0; p < 3; ++p) {
        producers.emplace_back([&queue, p]() {
            for (int i = 0; i < 5; ++i) {
                std::string msg = "Producer " + std::to_string(p) +
                                  " - Message " + std::to_string(i);
                while (!queue.enqueue(msg)) {
                    std::this_thread::yield();
                }
                std::cout << "Enqueued: " << msg << std::endl;
            }
        });
    }

    // Multiple consumers
    std::vector<std::thread> consumers;
    for (int c = 0; c < 2; ++c) {
        consumers.emplace_back([&queue, c]() {
            for (int i = 0; i < 7; ++i) { // Total 15 messages / 2 consumers
                std::string msg;
                while (!queue.dequeue(msg)) {
                    std::this_thread::yield();
                }
                std::cout << "Consumer " << c << " dequeued: " << msg << std::endl;
            }
        });
    }

    // Wait for completion
    for (auto& t : producers) t.join();

    // Dequeue remaining message
    std::string msg;
    if (queue.dequeue(msg)) {
        std::cout << "Final message: " << msg << std::endl;
    }

    for (auto& t : consumers) t.join();
}

// Example 3: Bulk Operations
void example_bulk_operations() {
    std::cout << "\n=== Example 3: Bulk Operations ===" << std::endl;

    MPMCQueue<int> queue(1024);

    // Bulk enqueue
    std::vector<int> data(100);
    std::iota(data.begin(), data.end(), 1); // Fill with 1..100

    size_t enqueued = queue.enqueue_bulk(data.begin(), data.end());
    std::cout << "Bulk enqueued " << enqueued << " items" << std::endl;

    // Bulk dequeue
    std::vector<int> results(50);
    size_t dequeued = queue.dequeue_bulk(results.begin(), 50);
    std::cout << "Bulk dequeued " << dequeued << " items" << std::endl;

    std::cout << "First dequeued item: " << results[0] << std::endl;
    std::cout << "Last dequeued item: " << results[dequeued - 1] << std::endl;
    std::cout << "Queue size: " << queue.size() << std::endl;
}

// Example 4: High-Frequency Producer-Consumer
void example_high_frequency() {
    std::cout << "\n=== Example 4: High-Frequency SPSC ===" << std::endl;

    const size_t NUM_ITEMS = 1000000;
    SPSCQueue<size_t> queue(1024);

    std::atomic<bool> done{false};
    std::atomic<size_t> consumed{0};

    auto start = std::chrono::high_resolution_clock::now();

    // Producer
    std::thread producer([&]() {
        for (size_t i = 0; i < NUM_ITEMS; ++i) {
            while (!queue.enqueue(i)) {
                std::this_thread::yield();
            }
        }
        done = true;
    });

    // Consumer
    std::thread consumer([&]() {
        size_t value;
        while (!done || !queue.empty()) {
            if (queue.dequeue(value)) {
                consumed++;
            } else {
                std::this_thread::yield();
            }
        }
    });

    producer.join();
    consumer.join();

    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Processed " << consumed << " items in " << duration.count() << "ms" << std::endl;
    std::cout << "Throughput: " << (consumed * 1000.0 / duration.count()) << " ops/sec" << std::endl;
}

// Example 5: Multiple Producers, Single Consumer
void example_mpsc() {
    std::cout << "\n=== Example 5: Multiple Producers, Single Consumer ===" << std::endl;

    const size_t NUM_PRODUCERS = 4;
    const size_t ITEMS_PER_PRODUCER = 1000;
    MPMCQueue<size_t> queue(1024);

    std::atomic<size_t> total_consumed{0};
    std::atomic<bool> done{false};

    // Multiple producers
    std::vector<std::thread> producers;
    for (size_t p = 0; p < NUM_PRODUCERS; ++p) {
        producers.emplace_back([&queue, p]() {
            for (size_t i = 0; i < ITEMS_PER_PRODUCER; ++i) {
                size_t value = p * ITEMS_PER_PRODUCER + i;
                while (!queue.enqueue(value)) {
                    std::this_thread::yield();
                }
            }
        });
    }

    // Single consumer
    std::thread consumer([&]() {
        size_t value;
        size_t expected_total = NUM_PRODUCERS * ITEMS_PER_PRODUCER;

        while (total_consumed < expected_total) {
            if (queue.dequeue(value)) {
                total_consumed++;
            } else if (done) {
                // Producers are done, but queue might still have items
                std::this_thread::yield();
            }
        }
    });

    for (auto& t : producers) t.join();
    done = true;
    consumer.join();

    std::cout << "Total consumed: " << total_consumed << std::endl;
    std::cout << "Expected: " << (NUM_PRODUCERS * ITEMS_PER_PRODUCER) << std::endl;
}

// Example 6: Benchmark SPSC vs MPMC
void benchmark_spsc_vs_mpmc() {
    std::cout << "\n=== Example 6: Benchmark SPSC vs MPMC ===" << std::endl;

    const size_t NUM_ITEMS = 5000000;

    // Benchmark SPSC
    {
        SPSCQueue<size_t> queue(1024);
        std::atomic<bool> done{false};

        auto start = std::chrono::high_resolution_clock::now();

        std::thread producer([&]() {
            for (size_t i = 0; i < NUM_ITEMS; ++i) {
                while (!queue.enqueue(i)) {
                    std::this_thread::yield();
                }
            }
            done = true;
        });

        std::thread consumer([&]() {
            size_t value;
            size_t count = 0;
            while (count < NUM_ITEMS) {
                if (queue.dequeue(value)) {
                    count++;
                }
            }
        });

        producer.join();
        consumer.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << "SPSC: " << NUM_ITEMS << " items in " << duration.count() << "ms" << std::endl;
        std::cout << "SPSC Throughput: " << (NUM_ITEMS * 1000.0 / duration.count()) / 1000000.0
                  << "M ops/sec" << std::endl;
    }

    // Benchmark MPMC (single producer, single consumer for fair comparison)
    {
        MPMCQueue<size_t> queue(1024);
        std::atomic<bool> done{false};

        auto start = std::chrono::high_resolution_clock::now();

        std::thread producer([&]() {
            for (size_t i = 0; i < NUM_ITEMS; ++i) {
                while (!queue.enqueue(i)) {
                    std::this_thread::yield();
                }
            }
            done = true;
        });

        std::thread consumer([&]() {
            size_t value;
            size_t count = 0;
            while (count < NUM_ITEMS) {
                if (queue.dequeue(value)) {
                    count++;
                }
            }
        });

        producer.join();
        consumer.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << "MPMC: " << NUM_ITEMS << " items in " << duration.count() << "ms" << std::endl;
        std::cout << "MPMC Throughput: " << (NUM_ITEMS * 1000.0 / duration.count()) / 1000000.0
                  << "M ops/sec" << std::endl;
    }
}

// Example 7: MPMC Scaling Test
void example_mpmc_scaling() {
    std::cout << "\n=== Example 7: MPMC Scaling Test ===" << std::endl;

    const size_t TOTAL_ITEMS = 1000000;
    const std::vector<size_t> thread_counts = {1, 2, 4, 8};

    for (size_t num_threads : thread_counts) {
        MPMCQueue<size_t> queue(1024);
        std::atomic<size_t> produced{0};
        std::atomic<size_t> consumed{0};

        auto start = std::chrono::high_resolution_clock::now();

        // Producers
        std::vector<std::thread> producers;
        size_t items_per_producer = TOTAL_ITEMS / num_threads;
        for (size_t i = 0; i < num_threads; ++i) {
            producers.emplace_back([&]() {
                for (size_t j = 0; j < items_per_producer; ++j) {
                    while (!queue.enqueue(j)) {
                        std::this_thread::yield();
                    }
                    produced++;
                }
            });
        }

        // Consumers
        std::vector<std::thread> consumers;
        for (size_t i = 0; i < num_threads; ++i) {
            consumers.emplace_back([&]() {
                size_t value;
                while (consumed < TOTAL_ITEMS) {
                    if (queue.dequeue(value)) {
                        consumed++;
                    }
                }
            });
        }

        for (auto& t : producers) t.join();
        for (auto& t : consumers) t.join();

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

        std::cout << num_threads << " threads: " << TOTAL_ITEMS << " items in "
                  << duration.count() << "ms ("
                  << (TOTAL_ITEMS * 1000.0 / duration.count()) / 1000000.0
                  << "M ops/sec)" << std::endl;
    }
}

// Example 8: Try Operations
void example_try_operations() {
    std::cout << "\n=== Example 8: Try Operations ===" << std::endl;

    MPMCQueue<int> queue(4); // Small queue to demonstrate full condition

    // Fill the queue
    for (int i = 0; i < 4; ++i) {
        if (queue.try_enqueue(i)) {
            std::cout << "Enqueued: " << i << std::endl;
        }
    }

    // Try to enqueue when full
    if (!queue.try_enqueue(999)) {
        std::cout << "Failed to enqueue 999 (queue is full)" << std::endl;
    }

    std::cout << "Queue is full: " << (queue.full() ? "yes" : "no") << std::endl;

    // Dequeue some items
    int value;
    for (int i = 0; i < 2; ++i) {
        if (queue.try_dequeue(value)) {
            std::cout << "Dequeued: " << value << std::endl;
        }
    }

    // Now we can enqueue again
    if (queue.try_enqueue(100)) {
        std::cout << "Successfully enqueued 100" << std::endl;
    }

    std::cout << "Final queue size: " << queue.size() << std::endl;
}

int main() {
    std::cout << "=== LockFreeQueue Example Demo ===" << std::endl;
    std::cout << "Hardware concurrency: " << std::thread::hardware_concurrency() << std::endl;

    example_spsc_basic();
    example_mpmc_basic();
    example_bulk_operations();
    example_high_frequency();
    example_mpsc();
    benchmark_spsc_vs_mpmc();
    example_mpmc_scaling();
    example_try_operations();

    std::cout << "\n=== All examples completed ===" << std::endl;
    return 0;
}
