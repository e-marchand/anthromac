cmake_minimum_required(VERSION 3.15)
project(ThreadPool VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(ThreadPool INTERFACE)
target_include_directories(ThreadPool INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(threadpool_example example.cpp)
target_link_libraries(threadpool_example PRIVATE ThreadPool)

# Compiler warnings
if(MSVC)
    target_compile_options(threadpool_example PRIVATE /W4)
else()
    target_compile_options(threadpool_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Enable threading
find_package(Threads REQUIRED)
target_link_libraries(threadpool_example PRIVATE Threads::Threads)

# Installation
install(FILES ThreadPool.hpp DESTINATION include)
