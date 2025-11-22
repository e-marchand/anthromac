cmake_minimum_required(VERSION 3.15)
project(JsonParser VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(JsonParser INTERFACE)
target_include_directories(JsonParser INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(jsonparser_example example.cpp)
target_link_libraries(jsonparser_example PRIVATE JsonParser)

# Compiler warnings
if(MSVC)
    target_compile_options(jsonparser_example PRIVATE /W4)
else()
    target_compile_options(jsonparser_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Optimization flags for release builds
if(NOT MSVC)
    target_compile_options(jsonparser_example PRIVATE
        $<$<CONFIG:RELEASE>:-O3 -march=native>
    )
endif()

# Installation
install(FILES JsonParser.hpp DESTINATION include)
