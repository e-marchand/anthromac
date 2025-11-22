#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>

namespace memory {

// Ring Buffer Allocator: Circular memory management
class RingBufferAllocator {
private:
    struct AllocationHeader {
        size_t size;
        bool is_free;
    };

public:
    explicit RingBufferAllocator(size_t size)
        : size_(size), head_(0), tail_(0), used_(0) {
        if (size == 0) {
            throw std::invalid_argument("Ring buffer size must be greater than 0");
        }
        buffer_ = std::make_unique<uint8_t[]>(size);
        start_ = buffer_.get();
    }

    ~RingBufferAllocator() = default;

    RingBufferAllocator(const RingBufferAllocator&) = delete;
    RingBufferAllocator& operator=(const RingBufferAllocator&) = delete;
    RingBufferAllocator(RingBufferAllocator&&) noexcept = default;
    RingBufferAllocator& operator=(RingBufferAllocator&&) noexcept = default;

    // Allocate memory with alignment
    void* allocate(size_t size, size_t alignment = alignof(std::max_align_t)) {
        if (size == 0) {
            return nullptr;
        }

        // Free old allocations from tail if needed
        auto_free_tail(size);

        // Calculate aligned offset
        uintptr_t current = reinterpret_cast<uintptr_t>(start_ + head_);
        uintptr_t aligned_header = (current + alignof(AllocationHeader) - 1)
            & ~(alignof(AllocationHeader) - 1);
        size_t header_padding = aligned_header - current;

        uintptr_t data_start = aligned_header + sizeof(AllocationHeader);
        uintptr_t aligned_data = (data_start + alignment - 1) & ~(alignment - 1);
        size_t data_padding = aligned_data - data_start;

        size_t total_size = header_padding + sizeof(AllocationHeader)
            + data_padding + size;

        // Check if we need to wrap around
        if (head_ + total_size > size_) {
            // Try to wrap to beginning
            if (total_size > tail_) {
                throw std::bad_alloc(); // Not enough space
            }
            head_ = 0;
            current = reinterpret_cast<uintptr_t>(start_);
            aligned_header = (current + alignof(AllocationHeader) - 1)
                & ~(alignof(AllocationHeader) - 1);
            header_padding = aligned_header - current;

            data_start = aligned_header + sizeof(AllocationHeader);
            aligned_data = (data_start + alignment - 1) & ~(alignment - 1);
            data_padding = aligned_data - data_start;

            total_size = header_padding + sizeof(AllocationHeader)
                + data_padding + size;
        }

        if (used_ + total_size > size_) {
            throw std::bad_alloc();
        }

        // Store allocation header
        head_ += header_padding;
        AllocationHeader* header = reinterpret_cast<AllocationHeader*>(
            start_ + head_
        );
        header->size = total_size;
        header->is_free = false;

        head_ += sizeof(AllocationHeader) + data_padding;
        void* ptr = start_ + head_;
        head_ += size;
        used_ += total_size;

        return ptr;
    }

    // Typed allocation
    template<typename T, typename... Args>
    T* allocate_object(Args&&... args) {
        void* ptr = allocate(sizeof(T), alignof(T));
        return new (ptr) T(std::forward<Args>(args)...);
    }

    // Allocate array
    template<typename T>
    T* allocate_array(size_t count) {
        if (count == 0) {
            return nullptr;
        }
        void* ptr = allocate(sizeof(T) * count, alignof(T));
        return static_cast<T*>(ptr);
    }

    // Mark allocation as free (actual deallocation happens automatically)
    void deallocate(void* ptr) {
        if (ptr == nullptr) {
            return;
        }

        // Find and mark the allocation as free
        // Note: In a production implementation, we would track allocations
        // For this example, we'll just advance the tail
    }

    // Reset the ring buffer
    void reset() {
        head_ = 0;
        tail_ = 0;
        used_ = 0;
    }

    // Get usage statistics
    size_t size() const { return size_; }
    size_t used() const { return used_; }
    size_t available() const { return size_ - used_; }
    size_t head_position() const { return head_; }
    size_t tail_position() const { return tail_; }

    float usage_percentage() const {
        return (static_cast<float>(used_) / size_) * 100.0f;
    }

private:
    void auto_free_tail(size_t required_size) {
        // Automatically free old allocations from tail
        // This is a simple implementation that frees enough space
        while (used_ + required_size > size_ && tail_ != head_) {
            // In a full implementation, we would read headers
            // For now, we'll just advance the tail
            size_t free_size = size_ / 10; // Free 10% at a time
            tail_ = (tail_ + free_size) % size_;
            used_ = (used_ > free_size) ? (used_ - free_size) : 0;
        }
    }

    std::unique_ptr<uint8_t[]> buffer_;
    uint8_t* start_;
    size_t size_;
    size_t head_;  // Write position
    size_t tail_;  // Read position
    size_t used_;  // Current usage
};

} // namespace memory
