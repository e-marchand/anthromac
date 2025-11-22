#pragma once

#include <cstddef>
#include <cstdint>
#include <memory>
#include <stdexcept>

namespace memory {

// Arena Allocator: Linear allocation with bulk deallocation
class ArenaAllocator {
public:
    explicit ArenaAllocator(size_t size)
        : size_(size), used_(0) {
        if (size == 0) {
            throw std::invalid_argument("Arena size must be greater than 0");
        }
        buffer_ = std::make_unique<uint8_t[]>(size);
        start_ = buffer_.get();
    }

    ~ArenaAllocator() = default;

    // Non-copyable, movable
    ArenaAllocator(const ArenaAllocator&) = delete;
    ArenaAllocator& operator=(const ArenaAllocator&) = delete;
    ArenaAllocator(ArenaAllocator&&) noexcept = default;
    ArenaAllocator& operator=(ArenaAllocator&&) noexcept = default;

    // Allocate memory with alignment
    void* allocate(size_t size, size_t alignment = alignof(std::max_align_t)) {
        if (size == 0) {
            return nullptr;
        }

        // Calculate aligned offset
        uintptr_t current = reinterpret_cast<uintptr_t>(start_ + used_);
        uintptr_t aligned = (current + alignment - 1) & ~(alignment - 1);
        size_t padding = aligned - current;

        if (used_ + padding + size > size_) {
            throw std::bad_alloc();
        }

        used_ += padding;
        void* ptr = start_ + used_;
        used_ += size;

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

    // Reset the arena (deallocate all)
    void reset() {
        used_ = 0;
    }

    // Get usage statistics
    size_t size() const { return size_; }
    size_t used() const { return used_; }
    size_t available() const { return size_ - used_; }
    float usage_percentage() const {
        return (static_cast<float>(used_) / size_) * 100.0f;
    }

private:
    std::unique_ptr<uint8_t[]> buffer_;
    uint8_t* start_;
    size_t size_;
    size_t used_;
};

} // namespace memory
