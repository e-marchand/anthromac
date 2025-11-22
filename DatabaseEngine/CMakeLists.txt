cmake_minimum_required(VERSION 3.15)
project(DatabaseEngine)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Header-only library
add_library(database_engine INTERFACE)
target_include_directories(database_engine INTERFACE ${CMAKE_CURRENT_SOURCE_DIR})

# Example executable
add_executable(db_example example.cpp)
target_link_libraries(db_example PRIVATE database_engine)

# Link filesystem library if needed (GCC < 9)
if(CMAKE_CXX_COMPILER_ID STREQUAL "GNU" AND CMAKE_CXX_COMPILER_VERSION VERSION_LESS 9.0)
    target_link_libraries(db_example PRIVATE stdc++fs)
endif()

# Enable optimizations for release builds
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    if(NOT MSVC)
        target_compile_options(db_example PRIVATE -O3)
    endif()
endif()

# Compiler warnings
if(MSVC)
    target_compile_options(db_example PRIVATE /W4)
else()
    target_compile_options(db_example PRIVATE -Wall -Wextra)
endif()
