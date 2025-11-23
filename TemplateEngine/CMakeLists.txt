cmake_minimum_required(VERSION 3.15)
project(TemplateEngine)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(template_engine INTERFACE)
target_include_directories(template_engine INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable
add_executable(template_example example.cpp)
target_link_libraries(template_example PRIVATE template_engine)

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(NOT MSVC)
        target_compile_options(template_example PRIVATE -O3)
    endif()
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(template_example PRIVATE /W4)
else()
    target_compile_options(template_example PRIVATE -Wall -Wextra)
endif()
