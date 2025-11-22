#pragma once

// MemoryArena - Fast Custom Memory Management
// A collection of high-performance memory allocators

#include "ArenaAllocator.hpp"
#include "PoolAllocator.hpp"
#include "StackAllocator.hpp"
#include "RingBufferAllocator.hpp"

namespace memory {

// Version information
constexpr int VERSION_MAJOR = 1;
constexpr int VERSION_MINOR = 0;
constexpr int VERSION_PATCH = 0;

} // namespace memory
