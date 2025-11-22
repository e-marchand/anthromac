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
