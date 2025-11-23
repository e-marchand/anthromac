cmake_minimum_required(VERSION 3.15)
project(ConfigParser)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(config_parser INTERFACE)
target_include_directories(config_parser INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable
add_executable(config_example example.cpp)
target_link_libraries(config_example PRIVATE config_parser)

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(NOT MSVC)
        target_compile_options(config_example PRIVATE -O3)
    endif()
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(config_example PRIVATE /W4)
else()
    target_compile_options(config_example PRIVATE -Wall -Wextra)
endif()
