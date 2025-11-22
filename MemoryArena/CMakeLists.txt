cmake_minimum_required(VERSION 3.15)
project(MemoryArena VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(MemoryArena INTERFACE)
target_include_directories(MemoryArena INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(memoryarena_example example.cpp)
target_link_libraries(memoryarena_example PRIVATE MemoryArena)

# Compiler warnings
if(MSVC)
    target_compile_options(memoryarena_example PRIVATE /W4)
else()
    target_compile_options(memoryarena_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Installation
install(FILES
    MemoryArena.hpp
    ArenaAllocator.hpp
    PoolAllocator.hpp
    StackAllocator.hpp
    RingBufferAllocator.hpp
    DESTINATION include
)
