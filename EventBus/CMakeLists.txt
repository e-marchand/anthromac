cmake_minimum_required(VERSION 3.15)
project(EventBus VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(EventBus INTERFACE)
target_include_directories(EventBus INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(eventbus_example example.cpp)
target_link_libraries(eventbus_example PRIVATE EventBus)

# Compiler warnings
if(MSVC)
    target_compile_options(eventbus_example PRIVATE /W4)
else()
    target_compile_options(eventbus_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Enable threading
find_package(Threads REQUIRED)
target_link_libraries(eventbus_example PRIVATE Threads::Threads)

# Installation
install(FILES EventBus.hpp DESTINATION include)
