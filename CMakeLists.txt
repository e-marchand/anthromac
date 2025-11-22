cmake_minimum_required(VERSION 3.15)
project(AnthroMac VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# Add subdirectories
add_subdirectory(ThreadPool)
add_subdirectory(MemoryArena)
add_subdirectory(EventBus)
add_subdirectory(LockFreeQueue)
add_subdirectory(JsonParser)
add_subdirectory(NetworkStack)
add_subdirectory(Reflection)

# Enable testing
enable_testing()

message(STATUS "AnthroMac C++ Projects configured successfully")
message(STATUS "  - ThreadPool: High-Performance Task Scheduler")
message(STATUS "  - MemoryArena: Custom Memory Management")
message(STATUS "  - EventBus: Modern Event System")
message(STATUS "  - LockFreeQueue: Lock-Free MPMC Queue")
message(STATUS "  - JsonParser: High-Performance JSON Processing")
message(STATUS "  - NetworkStack: Async Networking Library")
message(STATUS "  - Reflection: Compile-Time Reflection System")
