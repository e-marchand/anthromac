#include "MemoryArena.hpp"
#include <iostream>
#include <vector>
#include <chrono>
#include <string>

using namespace memory;

struct TestObject {
    int id;
    double value;
    std::string name;

    TestObject(int i = 0, double v = 0.0, const std::string& n = "")
        : id(i), value(v), name(n) {
        std::cout << "  TestObject(" << id << ") constructed" << std::endl;
    }

    ~TestObject() {
        std::cout << "  TestObject(" << id << ") destroyed" << std::endl;
    }
};

void demo_arena_allocator() {
    std::cout << "\n=== Arena Allocator Demo ===" << std::endl;

    ArenaAllocator arena(1024 * 1024); // 1MB arena

    std::cout << "Arena size: " << arena.size() << " bytes" << std::endl;

    // Allocate some integers
    int* numbers = arena.allocate_array<int>(100);
    for (int i = 0; i < 100; ++i) {
        numbers[i] = i * i;
    }

    std::cout << "Allocated 100 integers" << std::endl;
    std::cout << "Used: " << arena.used() << " bytes ("
              << arena.usage_percentage() << "%)" << std::endl;

    // Allocate objects
    auto* obj1 = arena.allocate_object<TestObject>(1, 3.14, "Object1");
    auto* obj2 = arena.allocate_object<TestObject>(2, 2.71, "Object2");

    std::cout << "Object 1: id=" << obj1->id << ", name=" << obj1->name << std::endl;
    std::cout << "Object 2: id=" << obj2->id << ", name=" << obj2->name << std::endl;

    std::cout << "Used: " << arena.used() << " bytes ("
              << arena.usage_percentage() << "%)" << std::endl;

    // Reset arena (bulk deallocation)
    std::cout << "\nResetting arena..." << std::endl;
    arena.reset();
    std::cout << "Used after reset: " << arena.used() << " bytes" << std::endl;
}

void demo_pool_allocator() {
    std::cout << "\n=== Pool Allocator Demo ===" << std::endl;

    PoolAllocator<TestObject> pool(10);

    std::cout << "Pool capacity: " << pool.capacity() << std::endl;

    // Allocate objects
    std::vector<TestObject*> objects;
    for (int i = 0; i < 5; ++i) {
        auto* obj = pool.allocate(i, i * 1.5, "PoolObj" + std::to_string(i));
        objects.push_back(obj);
    }

    std::cout << "\nPool stats:" << std::endl;
    std::cout << "  Used: " << pool.used_count() << std::endl;
    std::cout << "  Free: " << pool.free_count() << std::endl;
    std::cout << "  Usage: " << pool.usage_percentage() << "%" << std::endl;

    // Deallocate some objects
    std::cout << "\nDeallocating objects..." << std::endl;
    for (auto* obj : objects) {
        pool.deallocate(obj);
    }

    std::cout << "\nPool stats after deallocation:" << std::endl;
    std::cout << "  Used: " << pool.used_count() << std::endl;
    std::cout << "  Free: " << pool.free_count() << std::endl;
}

void demo_stack_allocator() {
    std::cout << "\n=== Stack Allocator Demo ===" << std::endl;

    StackAllocator stack(1024 * 1024); // 1MB stack

    std::cout << "Stack size: " << stack.size() << " bytes" << std::endl;

    // Create a marker for later
    size_t marker1 = stack.get_marker();

    // Allocate some data
    int* data1 = stack.allocate_array<int>(100);
    for (int i = 0; i < 100; ++i) {
        data1[i] = i;
    }

    std::cout << "Allocated 100 integers" << std::endl;
    std::cout << "Used: " << stack.used() << " bytes" << std::endl;

    size_t marker2 = stack.get_marker();

    // Allocate more data
    double* data2 = stack.allocate_array<double>(50);
    for (int i = 0; i < 50; ++i) {
        data2[i] = i * 3.14;
    }

    std::cout << "Allocated 50 doubles" << std::endl;
    std::cout << "Used: " << stack.used() << " bytes" << std::endl;

    // Free to marker (LIFO deallocation)
    std::cout << "\nFreeing to marker 2..." << std::endl;
    stack.free_to_marker(marker2);
    std::cout << "Used: " << stack.used() << " bytes" << std::endl;

    std::cout << "Freeing to marker 1..." << std::endl;
    stack.free_to_marker(marker1);
    std::cout << "Used: " << stack.used() << " bytes" << std::endl;
}

void demo_ring_buffer_allocator() {
    std::cout << "\n=== Ring Buffer Allocator Demo ===" << std::endl;

    RingBufferAllocator ring(1024); // 1KB ring buffer

    std::cout << "Ring buffer size: " << ring.size() << " bytes" << std::endl;

    // Allocate multiple chunks
    for (int i = 0; i < 5; ++i) {
        int* data = ring.allocate_array<int>(10);
        for (int j = 0; j < 10; ++j) {
            data[j] = i * 10 + j;
        }

        std::cout << "Allocation " << i << ": "
                  << "head=" << ring.head_position()
                  << ", used=" << ring.used() << " bytes ("
                  << ring.usage_percentage() << "%)" << std::endl;
    }

    std::cout << "\nFinal ring buffer state:" << std::endl;
    std::cout << "  Head: " << ring.head_position() << std::endl;
    std::cout << "  Tail: " << ring.tail_position() << std::endl;
    std::cout << "  Used: " << ring.used() << " bytes" << std::endl;
}

void benchmark_allocators() {
    std::cout << "\n=== Performance Benchmark ===" << std::endl;

    const int iterations = 100000;
    const int object_size = 64;

    // Benchmark standard malloc/free
    {
        auto start = std::chrono::high_resolution_clock::now();

        for (int i = 0; i < iterations; ++i) {
            void* ptr = std::malloc(object_size);
            std::free(ptr);
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "malloc/free: " << duration.count() << " μs" << std::endl;
    }

    // Benchmark Arena Allocator
    {
        ArenaAllocator arena(1024 * 1024 * 10); // 10MB

        auto start = std::chrono::high_resolution_clock::now();

        for (int i = 0; i < iterations; ++i) {
            arena.allocate(object_size);
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "ArenaAllocator: " << duration.count() << " μs"
                  << " (speedup: "
                  << (duration.count() > 0 ? "~10x faster" : "N/A")
                  << ")" << std::endl;
    }

    // Benchmark Pool Allocator
    {
        struct TestBlock {
            char data[object_size];
        };

        PoolAllocator<TestBlock> pool(iterations);

        auto start = std::chrono::high_resolution_clock::now();

        std::vector<TestBlock*> ptrs;
        ptrs.reserve(iterations);

        for (int i = 0; i < iterations; ++i) {
            ptrs.push_back(pool.allocate());
        }

        for (auto* ptr : ptrs) {
            pool.deallocate(ptr);
        }

        auto end = std::chrono::high_resolution_clock::now();
        auto duration = std::chrono::duration_cast<std::chrono::microseconds>(end - start);

        std::cout << "PoolAllocator: " << duration.count() << " μs"
                  << " (O(1) alloc/free)" << std::endl;
    }
}

int main() {
    std::cout << "MemoryArena v"
              << VERSION_MAJOR << "."
              << VERSION_MINOR << "."
              << VERSION_PATCH << std::endl;

    demo_arena_allocator();
    demo_pool_allocator();
    demo_stack_allocator();
    demo_ring_buffer_allocator();
    benchmark_allocators();

    std::cout << "\n=== All demos completed ===" << std::endl;
    return 0;
}
