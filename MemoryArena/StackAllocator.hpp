#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>

namespace memory {

// Stack Allocator: LIFO allocation pattern
class StackAllocator {
private:
    struct AllocationHeader {
        size_t size;
        size_t padding;
    };

public:
    explicit StackAllocator(size_t size)
        : size_(size), offset_(0), prev_offset_(0) {
        if (size == 0) {
            throw std::invalid_argument("Stack size must be greater than 0");
        }
        buffer_ = std::make_unique<uint8_t[]>(size);
        start_ = buffer_.get();
    }

    ~StackAllocator() = default;

    StackAllocator(const StackAllocator&) = delete;
    StackAllocator& operator=(const StackAllocator&) = delete;
    StackAllocator(StackAllocator&&) noexcept = default;
    StackAllocator& operator=(StackAllocator&&) noexcept = default;

    // Allocate memory with alignment
    void* allocate(size_t size, size_t alignment = alignof(std::max_align_t)) {
        if (size == 0) {
            return nullptr;
        }

        // Calculate aligned offset for the header
        uintptr_t current = reinterpret_cast<uintptr_t>(start_ + offset_);
        uintptr_t aligned_header = (current + alignof(AllocationHeader) - 1)
            & ~(alignof(AllocationHeader) - 1);
        size_t header_padding = aligned_header - current;

        // Calculate aligned offset for the data
        uintptr_t data_start = aligned_header + sizeof(AllocationHeader);
        uintptr_t aligned_data = (data_start + alignment - 1) & ~(alignment - 1);
        size_t data_padding = aligned_data - data_start;

        size_t total_size = header_padding + sizeof(AllocationHeader)
            + data_padding + size;

        if (offset_ + total_size > size_) {
            throw std::bad_alloc();
        }

        // Store allocation info
        prev_offset_ = offset_;
        offset_ += header_padding;

        AllocationHeader* header = reinterpret_cast<AllocationHeader*>(
            start_ + offset_
        );
        header->size = total_size;
        header->padding = data_padding;

        offset_ += sizeof(AllocationHeader) + data_padding;
        void* ptr = start_ + offset_;
        offset_ += size;

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

    // Deallocate last allocation (LIFO)
    void deallocate(void* ptr) {
        if (ptr == nullptr) {
            return;
        }

        uintptr_t ptr_addr = reinterpret_cast<uintptr_t>(ptr);
        uintptr_t start_addr = reinterpret_cast<uintptr_t>(start_);

        if (ptr_addr < start_addr || ptr_addr >= start_addr + size_) {
            throw std::invalid_argument("Pointer not from this allocator");
        }

        // Get the header
        AllocationHeader* header = reinterpret_cast<AllocationHeader*>(
            reinterpret_cast<uint8_t*>(ptr) - sizeof(AllocationHeader)
            - reinterpret_cast<AllocationHeader*>(
                reinterpret_cast<uint8_t*>(ptr) - sizeof(AllocationHeader)
            )->padding
        );

        // Verify this is the last allocation
        size_t expected_offset = (reinterpret_cast<uint8_t*>(ptr) - start_)
            + (offset_ - (reinterpret_cast<uint8_t*>(ptr) - start_));

        // Roll back to previous offset
        offset_ = prev_offset_;
    }

    // Reset the stack
    void reset() {
        offset_ = 0;
        prev_offset_ = 0;
    }

    // Create a marker for bulk deallocation
    size_t get_marker() const {
        return offset_;
    }

    // Free to a marker
    void free_to_marker(size_t marker) {
        if (marker > offset_) {
            throw std::invalid_argument("Invalid marker");
        }
        offset_ = marker;
    }

    // Get usage statistics
    size_t size() const { return size_; }
    size_t used() const { return offset_; }
    size_t available() const { return size_ - offset_; }
    float usage_percentage() const {
        return (static_cast<float>(offset_) / size_) * 100.0f;
    }

private:
    std::unique_ptr<uint8_t[]> buffer_;
    uint8_t* start_;
    size_t size_;
    size_t offset_;
    size_t prev_offset_;
};

} // namespace memory
