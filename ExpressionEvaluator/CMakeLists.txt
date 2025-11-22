cmake_minimum_required(VERSION 3.15)
project(ExpressionEvaluator)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(expression_evaluator INTERFACE)
target_include_directories(expression_evaluator INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable
add_executable(expression_example example.cpp)
target_link_libraries(expression_example PRIVATE expression_evaluator)

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_compile_options(expression_example PRIVATE -O3)
endif()
