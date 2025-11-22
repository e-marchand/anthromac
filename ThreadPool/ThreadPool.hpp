#pragma once

#include <atomic>
#include <condition_variable>
#include <functional>
#include <future>
#include <memory>
#include <mutex>
#include <queue>
#include <thread>
#include <vector>
#include <random>
#include <type_traits>

namespace tp {

template<typename T>
class WorkStealingQueue {
private:
    std::deque<T> queue_;
    mutable std::mutex mutex_;

public:
    WorkStealingQueue() = default;
    WorkStealingQueue(const WorkStealingQueue&) = delete;
    WorkStealingQueue& operator=(const WorkStealingQueue&) = delete;

    void push(T value) {
        std::lock_guard<std::mutex> lock(mutex_);
        queue_.push_back(std::move(value));
    }

    bool pop(T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return false;
        }
        value = std::move(queue_.back());
        queue_.pop_back();
        return true;
    }

    bool steal(T& value) {
        std::lock_guard<std::mutex> lock(mutex_);
        if (queue_.empty()) {
            return false;
        }
        value = std::move(queue_.front());
        queue_.pop_front();
        return true;
    }

    bool empty() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.empty();
    }

    size_t size() const {
        std::lock_guard<std::mutex> lock(mutex_);
        return queue_.size();
    }
};

class ThreadPool {
public:
    using Task = std::function<void()>;

    explicit ThreadPool(size_t num_threads = std::thread::hardware_concurrency())
        : stop_(false), active_tasks_(0) {

        if (num_threads == 0) {
            num_threads = 1;
        }

        queues_.resize(num_threads);
        workers_.reserve(num_threads);

        for (size_t i = 0; i < num_threads; ++i) {
            workers_.emplace_back([this, i, num_threads] {
                worker_thread(i, num_threads);
            });
        }
    }

    ~ThreadPool() {
        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            stop_ = true;
        }
        condition_.notify_all();

        for (auto& worker : workers_) {
            if (worker.joinable()) {
                worker.join();
            }
        }
    }

    // Enqueue a task and return a future for the result
    template<typename F, typename... Args>
    auto enqueue(F&& f, Args&&... args)
        -> std::future<typename std::invoke_result_t<F, Args...>> {

        using return_type = typename std::invoke_result_t<F, Args...>;

        auto task = std::make_shared<std::packaged_task<return_type()>>(
            std::bind(std::forward<F>(f), std::forward<Args>(args)...)
        );

        std::future<return_type> result = task->get_future();

        {
            std::unique_lock<std::mutex> lock(queue_mutex_);
            if (stop_) {
                throw std::runtime_error("enqueue on stopped ThreadPool");
            }

            // Find the queue with the least work
            size_t min_queue = 0;
            size_t min_size = queues_[0].size();
            for (size_t i = 1; i < queues_.size(); ++i) {
                size_t size = queues_[i].size();
                if (size < min_size) {
                    min_size = size;
                    min_queue = i;
                }
            }

            queues_[min_queue].push([task]() { (*task)(); });
        }

        condition_.notify_one();
        return result;
    }

    // Get the number of worker threads
    size_t thread_count() const {
        return workers_.size();
    }

    // Get the number of active tasks
    size_t active_tasks() const {
        return active_tasks_.load();
    }

    // Wait for all tasks to complete
    void wait() {
        std::unique_lock<std::mutex> lock(queue_mutex_);
        complete_condition_.wait(lock, [this] {
            bool all_empty = true;
            for (const auto& queue : queues_) {
                if (!queue.empty()) {
                    all_empty = false;
                    break;
                }
            }
            return all_empty && active_tasks_.load() == 0;
        });
    }

private:
    void worker_thread(size_t thread_id, size_t num_threads) {
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_int_distribution<size_t> dist(0, num_threads - 1);

        while (true) {
            Task task;
            bool found = false;

            // Try to get task from own queue
            if (queues_[thread_id].pop(task)) {
                found = true;
            } else {
                // Work stealing: try to steal from other queues
                for (size_t i = 0; i < num_threads * 2; ++i) {
                    size_t steal_id = dist(gen);
                    if (steal_id != thread_id && queues_[steal_id].steal(task)) {
                        found = true;
                        break;
                    }
                }
            }

            if (found) {
                active_tasks_++;
                task();
                active_tasks_--;
                complete_condition_.notify_all();
            } else {
                std::unique_lock<std::mutex> lock(queue_mutex_);
                condition_.wait(lock, [this] {
                    bool has_work = false;
                    for (const auto& queue : queues_) {
                        if (!queue.empty()) {
                            has_work = true;
                            break;
                        }
                    }
                    return stop_ || has_work;
                });

                if (stop_) {
                    break;
                }
            }
        }
    }

    std::vector<std::thread> workers_;
    std::vector<WorkStealingQueue<Task>> queues_;

    mutable std::mutex queue_mutex_;
    std::condition_variable condition_;
    std::condition_variable complete_condition_;
    std::atomic<bool> stop_;
    std::atomic<size_t> active_tasks_;
};

} // namespace tp
