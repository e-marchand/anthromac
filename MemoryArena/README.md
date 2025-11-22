# MemoryArena - Fast Custom Memory Management

A collection of high-performance memory allocators optimized for different use cases, featuring arena allocation, object pools, and stack-based allocation strategies.

## Allocators Included
- Arena Allocator: Linear allocation with bulk deallocation
- Pool Allocator: Fixed-size object pooling with O(1) alloc/free
- Stack Allocator: LIFO allocation pattern
- Ring Buffer Allocator: Circular memory management

## Performance
- Up to 10x faster than standard malloc/free for small objects
- Zero fragmentation for arena allocator
- Cache-friendly memory access patterns

## Usage

### Arena Allocator
Best for: Temporary allocations that are freed all at once (e.g., per-frame game data, request handlers)

```cpp
#include "ArenaAllocator.hpp"
using namespace memory;

ArenaAllocator arena(1024 * 1024); // 1MB arena

// Allocate objects
int* numbers = arena.allocate_array<int>(100);
MyObject* obj = arena.allocate_object<MyObject>(arg1, arg2);

// Use the allocated memory...

// Free everything at once
arena.reset();
```

### Pool Allocator
Best for: Fixed-size objects with frequent allocation/deallocation (e.g., particles, nodes in a data structure)

```cpp
#include "PoolAllocator.hpp"
using namespace memory;

PoolAllocator<MyObject> pool(1000); // Pool for 1000 objects

// Allocate objects
MyObject* obj1 = pool.allocate(arg1, arg2);
MyObject* obj2 = pool.allocate(arg3, arg4);

// Deallocate specific objects
pool.deallocate(obj1);
pool.deallocate(obj2);
```

### Stack Allocator
Best for: LIFO allocation patterns (e.g., function call frames, nested scopes)

```cpp
#include "StackAllocator.hpp"
using namespace memory;

StackAllocator stack(1024 * 1024); // 1MB stack

// Create a marker
size_t marker = stack.get_marker();

// Allocate some data
int* data1 = stack.allocate_array<int>(100);
double* data2 = stack.allocate_array<double>(50);

// Free back to marker (LIFO)
stack.free_to_marker(marker);
```

### Ring Buffer Allocator
Best for: Circular buffers, streaming data, recent history (e.g., audio buffers, network packets)

```cpp
#include "RingBufferAllocator.hpp"
using namespace memory;

RingBufferAllocator ring(1024); // 1KB ring buffer

// Allocate chunks (old allocations automatically freed when needed)
for (int i = 0; i < 10; ++i) {
    int* data = ring.allocate_array<int>(10);
    // Use data...
    // Old allocations are automatically overwritten as buffer fills
}
```

## API Reference

### ArenaAllocator

**Constructor:**
- `ArenaAllocator(size_t size)` - Creates an arena of the specified size

**Methods:**
- `void* allocate(size_t size, size_t alignment = alignof(std::max_align_t))`
- `T* allocate_object<T>(Args&&... args)` - Allocate and construct object
- `T* allocate_array<T>(size_t count)` - Allocate array of objects
- `void reset()` - Free all allocations at once
- `size_t size() const` - Total arena size
- `size_t used() const` - Currently used bytes
- `size_t available() const` - Available bytes
- `float usage_percentage() const` - Usage as percentage

### PoolAllocator<T>

**Constructor:**
- `PoolAllocator(size_t capacity)` - Creates a pool for `capacity` objects

**Methods:**
- `T* allocate(Args&&... args)` - Allocate and construct object (O(1))
- `void deallocate(T* ptr)` - Destroy and free object (O(1))
- `size_t capacity() const` - Maximum number of objects
- `size_t free_count() const` - Number of free slots
- `size_t used_count() const` - Number of allocated objects
- `bool is_full() const` - Check if pool is full
- `bool is_empty() const` - Check if pool is empty

### StackAllocator

**Constructor:**
- `StackAllocator(size_t size)` - Creates a stack of the specified size

**Methods:**
- `void* allocate(size_t size, size_t alignment = alignof(std::max_align_t))`
- `T* allocate_object<T>(Args&&... args)` - Allocate and construct object
- `T* allocate_array<T>(size_t count)` - Allocate array
- `void deallocate(void* ptr)` - Deallocate last allocation (LIFO)
- `void reset()` - Free all allocations
- `size_t get_marker() const` - Get current position marker
- `void free_to_marker(size_t marker)` - Free to a previous marker

### RingBufferAllocator

**Constructor:**
- `RingBufferAllocator(size_t size)` - Creates a ring buffer of the specified size

**Methods:**
- `void* allocate(size_t size, size_t alignment = alignof(std::max_align_t))`
- `T* allocate_object<T>(Args&&... args)` - Allocate and construct object
- `T* allocate_array<T>(size_t count)` - Allocate array
- `void reset()` - Reset the ring buffer
- `size_t head_position() const` - Current write position
- `size_t tail_position() const` - Current read position

## Building

### As Header-Only Library
Include the allocator headers you need:

```cpp
#include "MemoryArena.hpp"  // Includes all allocators
// Or include specific allocators:
#include "ArenaAllocator.hpp"
#include "PoolAllocator.hpp"
```

### With CMake
```bash
cd MemoryArena
mkdir build && cd build
cmake ..
cmake --build .
./memoryarena_example
```

## When to Use Each Allocator

| Allocator | Use Case | Allocation | Deallocation | Fragmentation |
|-----------|----------|------------|--------------|---------------|
| Arena | Temporary bulk data | O(1) | Bulk O(1) | None |
| Pool | Fixed-size objects | O(1) | O(1) per object | None |
| Stack | LIFO patterns | O(1) | O(1) LIFO | None |
| Ring Buffer | Circular/streaming | O(1) | Automatic | None |

## Requirements
- C++20 compatible compiler
- Standard library support
