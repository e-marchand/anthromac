cmake_minimum_required(VERSION 3.15)
project(NetworkStack VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(NetworkStack INTERFACE)
target_include_directories(NetworkStack INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(networkstack_example example.cpp)
target_link_libraries(networkstack_example PRIVATE NetworkStack)

# Platform-specific libraries
if(WIN32)
    target_link_libraries(networkstack_example PRIVATE ws2_32)
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(networkstack_example PRIVATE /W4)
else()
    target_compile_options(networkstack_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Enable coroutines
if(CMAKE_CXX_COMPILER_ID MATCHES "GNU")
    target_compile_options(networkstack_example PRIVATE -fcoroutines)
elseif(CMAKE_CXX_COMPILER_ID MATCHES "Clang")
    target_compile_options(networkstack_example PRIVATE -fcoroutines-ts)
endif()

# Installation
install(FILES NetworkStack.hpp DESTINATION include)
