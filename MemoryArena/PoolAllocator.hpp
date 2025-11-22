#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>

namespace memory {

// Pool Allocator: Fixed-size object pooling with O(1) alloc/free
template<typename T>
class PoolAllocator {
private:
    union Node {
        T value;
        Node* next;

        Node() {}
        ~Node() {}
    };

public:
    explicit PoolAllocator(size_t capacity)
        : capacity_(capacity), free_count_(capacity) {
        if (capacity == 0) {
            throw std::invalid_argument("Pool capacity must be greater than 0");
        }

        // Allocate the pool
        buffer_ = std::make_unique<Node[]>(capacity);

        // Initialize free list
        free_list_ = &buffer_[0];
        for (size_t i = 0; i < capacity - 1; ++i) {
            buffer_[i].next = &buffer_[i + 1];
        }
        buffer_[capacity - 1].next = nullptr;
    }

    ~PoolAllocator() {
        // Note: Objects must be explicitly destroyed before pool destruction
    }

    PoolAllocator(const PoolAllocator&) = delete;
    PoolAllocator& operator=(const PoolAllocator&) = delete;

    // Allocate a single object
    template<typename... Args>
    T* allocate(Args&&... args) {
        if (free_list_ == nullptr) {
            throw std::bad_alloc();
        }

        Node* node = free_list_;
        free_list_ = node->next;
        --free_count_;

        // Construct object in-place
        return new (&node->value) T(std::forward<Args>(args)...);
    }

    // Deallocate an object
    void deallocate(T* ptr) {
        if (ptr == nullptr) {
            return;
        }

        // Destroy the object
        ptr->~T();

        // Return to free list
        Node* node = reinterpret_cast<Node*>(ptr);
        node->next = free_list_;
        free_list_ = node;
        ++free_count_;
    }

    // Get pool statistics
    size_t capacity() const { return capacity_; }
    size_t free_count() const { return free_count_; }
    size_t used_count() const { return capacity_ - free_count_; }
    bool is_full() const { return free_count_ == 0; }
    bool is_empty() const { return free_count_ == capacity_; }

    float usage_percentage() const {
        return (static_cast<float>(used_count()) / capacity_) * 100.0f;
    }

private:
    std::unique_ptr<Node[]> buffer_;
    Node* free_list_;
    size_t capacity_;
    size_t free_count_;
};

} // namespace memory
