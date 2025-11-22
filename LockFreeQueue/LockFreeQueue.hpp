#pragma once

#include <atomic>
#include <cstddef>
#include <memory>
#include <new>
#include <type_traits>
#include <utility>

namespace lockfree {

// Cache line size for padding
constexpr size_t CACHE_LINE_SIZE = 64;

// Helper to ensure capacity is power of 2
constexpr size_t next_power_of_2(size_t n) {
    n--;
    n |= n >> 1;
    n |= n >> 2;
    n |= n >> 4;
    n |= n >> 8;
    n |= n >> 16;
    n |= n >> 32;
    return n + 1;
}

// Single-Producer Single-Consumer Queue (Wait-Free)
template<typename T>
class SPSCQueue {
public:
    explicit SPSCQueue(size_t capacity)
        : capacity_(next_power_of_2(capacity))
        , mask_(capacity_ - 1)
        , buffer_(new Cell[capacity_])
        , head_(0)
        , tail_(0) {

        // Initialize sequence numbers
        for (size_t i = 0; i < capacity_; ++i) {
            buffer_[i].sequence.store(i, std::memory_order_relaxed);
        }
    }

    ~SPSCQueue() {
        // Clean up any remaining elements
        T item;
        while (dequeue(item)) {}
    }

    SPSCQueue(const SPSCQueue&) = delete;
    SPSCQueue& operator=(const SPSCQueue&) = delete;

    // Producer: Enqueue an item
    bool enqueue(const T& item) {
        return enqueue_impl(item);
    }

    bool enqueue(T&& item) {
        return enqueue_impl(std::move(item));
    }

    // Consumer: Dequeue an item
    bool dequeue(T& item) {
        size_t pos = tail_.load(std::memory_order_relaxed);
        Cell* cell = &buffer_[pos & mask_];

        size_t seq = cell->sequence.load(std::memory_order_acquire);
        intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos + 1);

        if (diff < 0) {
            return false; // Queue is empty
        }

        item = std::move(cell->data);
        cell->sequence.store(pos + capacity_, std::memory_order_release);
        tail_.store(pos + 1, std::memory_order_release);

        return true;
    }

    // Non-blocking try operations
    bool try_enqueue(const T& item) {
        return enqueue(item);
    }

    bool try_enqueue(T&& item) {
        return enqueue(std::move(item));
    }

    bool try_dequeue(T& item) {
        return dequeue(item);
    }

    // Query operations
    size_t size() const {
        size_t head = head_.load(std::memory_order_acquire);
        size_t tail = tail_.load(std::memory_order_acquire);
        return head - tail;
    }

    bool empty() const {
        return size() == 0;
    }

    bool full() const {
        return size() >= capacity_;
    }

    size_t capacity() const {
        return capacity_;
    }

private:
    template<typename U>
    bool enqueue_impl(U&& item) {
        size_t pos = head_.load(std::memory_order_relaxed);
        Cell* cell = &buffer_[pos & mask_];

        size_t seq = cell->sequence.load(std::memory_order_acquire);
        intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos);

        if (diff < 0) {
            return false; // Queue is full
        }

        cell->data = std::forward<U>(item);
        cell->sequence.store(pos + 1, std::memory_order_release);
        head_.store(pos + 1, std::memory_order_release);

        return true;
    }

    struct Cell {
        std::atomic<size_t> sequence;
        T data;
    };

    const size_t capacity_;
    const size_t mask_;
    std::unique_ptr<Cell[]> buffer_;

    // Cache-line aligned to prevent false sharing
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> head_;
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> tail_;
};

// Multi-Producer Multi-Consumer Queue (Lock-Free)
template<typename T>
class MPMCQueue {
public:
    explicit MPMCQueue(size_t capacity)
        : capacity_(next_power_of_2(capacity))
        , mask_(capacity_ - 1)
        , buffer_(new Cell[capacity_])
        , enqueue_pos_(0)
        , dequeue_pos_(0) {

        // Initialize sequence numbers
        for (size_t i = 0; i < capacity_; ++i) {
            buffer_[i].sequence.store(i, std::memory_order_relaxed);
        }
    }

    ~MPMCQueue() {
        // Clean up any remaining elements
        T item;
        while (dequeue(item)) {}
    }

    MPMCQueue(const MPMCQueue&) = delete;
    MPMCQueue& operator=(const MPMCQueue&) = delete;

    // Enqueue an item (thread-safe for multiple producers)
    bool enqueue(const T& item) {
        return enqueue_impl(item);
    }

    bool enqueue(T&& item) {
        return enqueue_impl(std::move(item));
    }

    // Dequeue an item (thread-safe for multiple consumers)
    bool dequeue(T& item) {
        Cell* cell;
        size_t pos = dequeue_pos_.load(std::memory_order_relaxed);

        for (;;) {
            cell = &buffer_[pos & mask_];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos + 1);

            if (diff == 0) {
                // Item is ready, try to claim it
                if (dequeue_pos_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                // Queue is empty
                return false;
            } else {
                // Another consumer got ahead, retry
                pos = dequeue_pos_.load(std::memory_order_relaxed);
            }
        }

        item = std::move(cell->data);
        cell->sequence.store(pos + capacity_, std::memory_order_release);

        return true;
    }

    // Try operations with retry limit
    bool try_enqueue(const T& item, size_t max_retries = 100) {
        return try_enqueue_impl(item, max_retries);
    }

    bool try_enqueue(T&& item, size_t max_retries = 100) {
        return try_enqueue_impl(std::move(item), max_retries);
    }

    bool try_dequeue(T& item, size_t max_retries = 100) {
        Cell* cell;
        size_t pos = dequeue_pos_.load(std::memory_order_relaxed);
        size_t retries = 0;

        for (;;) {
            if (retries++ >= max_retries) {
                return false;
            }

            cell = &buffer_[pos & mask_];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos + 1);

            if (diff == 0) {
                if (dequeue_pos_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                return false;
            } else {
                pos = dequeue_pos_.load(std::memory_order_relaxed);
            }
        }

        item = std::move(cell->data);
        cell->sequence.store(pos + capacity_, std::memory_order_release);

        return true;
    }

    // Bulk enqueue
    template<typename Iterator>
    size_t enqueue_bulk(Iterator begin, Iterator end) {
        size_t count = 0;
        for (auto it = begin; it != end; ++it) {
            if (!enqueue(*it)) {
                break;
            }
            ++count;
        }
        return count;
    }

    // Bulk dequeue
    template<typename Iterator>
    size_t dequeue_bulk(Iterator begin, size_t max_count) {
        size_t count = 0;
        for (size_t i = 0; i < max_count; ++i) {
            if (!dequeue(*begin)) {
                break;
            }
            ++begin;
            ++count;
        }
        return count;
    }

    // Query operations (approximate due to concurrent access)
    size_t size() const {
        size_t head = enqueue_pos_.load(std::memory_order_acquire);
        size_t tail = dequeue_pos_.load(std::memory_order_acquire);
        return head - tail;
    }

    bool empty() const {
        return size() == 0;
    }

    bool full() const {
        return size() >= capacity_;
    }

    size_t capacity() const {
        return capacity_;
    }

private:
    template<typename U>
    bool enqueue_impl(U&& item) {
        Cell* cell;
        size_t pos = enqueue_pos_.load(std::memory_order_relaxed);

        for (;;) {
            cell = &buffer_[pos & mask_];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos);

            if (diff == 0) {
                // Slot is available, try to claim it
                if (enqueue_pos_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                // Queue is full
                return false;
            } else {
                // Another producer got ahead, retry
                pos = enqueue_pos_.load(std::memory_order_relaxed);
            }
        }

        cell->data = std::forward<U>(item);
        cell->sequence.store(pos + 1, std::memory_order_release);

        return true;
    }

    template<typename U>
    bool try_enqueue_impl(U&& item, size_t max_retries) {
        Cell* cell;
        size_t pos = enqueue_pos_.load(std::memory_order_relaxed);
        size_t retries = 0;

        for (;;) {
            if (retries++ >= max_retries) {
                return false;
            }

            cell = &buffer_[pos & mask_];
            size_t seq = cell->sequence.load(std::memory_order_acquire);
            intptr_t diff = static_cast<intptr_t>(seq) - static_cast<intptr_t>(pos);

            if (diff == 0) {
                if (enqueue_pos_.compare_exchange_weak(pos, pos + 1, std::memory_order_relaxed)) {
                    break;
                }
            } else if (diff < 0) {
                return false;
            } else {
                pos = enqueue_pos_.load(std::memory_order_relaxed);
            }
        }

        cell->data = std::forward<U>(item);
        cell->sequence.store(pos + 1, std::memory_order_release);

        return true;
    }

    struct Cell {
        std::atomic<size_t> sequence;
        T data;
    };

    const size_t capacity_;
    const size_t mask_;
    std::unique_ptr<Cell[]> buffer_;

    // Cache-line aligned to prevent false sharing
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> enqueue_pos_;
    alignas(CACHE_LINE_SIZE) std::atomic<size_t> dequeue_pos_;
};

} // namespace lockfree
