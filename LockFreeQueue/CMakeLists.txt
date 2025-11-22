cmake_minimum_required(VERSION 3.15)
project(LockFreeQueue VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(LockFreeQueue INTERFACE)
target_include_directories(LockFreeQueue INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(lockfreequeue_example example.cpp)
target_link_libraries(lockfreequeue_example PRIVATE LockFreeQueue)

# Compiler warnings
if(MSVC)
    target_compile_options(lockfreequeue_example PRIVATE /W4)
else()
    target_compile_options(lockfreequeue_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Enable threading
find_package(Threads REQUIRED)
target_link_libraries(lockfreequeue_example PRIVATE Threads::Threads)

# Optimization flags for release builds
if(NOT MSVC)
    target_compile_options(lockfreequeue_example PRIVATE
        $<$<CONFIG:RELEASE>:-O3 -march=native>
    )
endif()

# Installation
install(FILES LockFreeQueue.hpp DESTINATION include)
