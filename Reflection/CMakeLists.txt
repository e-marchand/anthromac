cmake_minimum_required(VERSION 3.15)
project(Reflection VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Header-only library
add_library(Reflection INTERFACE)
target_include_directories(Reflection INTERFACE
    $<BUILD_INTERFACE:${CMAKE_CURRENT_SOURCE_DIR}>
    $<INSTALL_INTERFACE:include>
)

# Example executable
add_executable(reflection_example example.cpp)
target_link_libraries(reflection_example PRIVATE Reflection)

# Compiler warnings
if(MSVC)
    target_compile_options(reflection_example PRIVATE /W4)
else()
    target_compile_options(reflection_example PRIVATE -Wall -Wextra -Wpedantic)
endif()

# Optimization flags for release builds
if(NOT MSVC)
    target_compile_options(reflection_example PRIVATE
        $<$<CONFIG:RELEASE>:-O3>
    )
endif()

# Installation
install(FILES Reflection.hpp DESTINATION include)
