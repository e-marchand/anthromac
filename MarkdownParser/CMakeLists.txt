cmake_minimum_required(VERSION 3.15)
project(MarkdownParser)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(markdown_parser INTERFACE)
target_include_directories(markdown_parser INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable
add_executable(markdown_example example.cpp)
target_link_libraries(markdown_example PRIVATE markdown_parser)

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(NOT MSVC)
        target_compile_options(markdown_example PRIVATE -O3)
    endif()
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(markdown_example PRIVATE /W4)
else()
    target_compile_options(markdown_example PRIVATE -Wall -Wextra)
endif()
