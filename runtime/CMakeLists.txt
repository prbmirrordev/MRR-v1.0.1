cmake_minimum_required(VERSION 3.20)
project(mrr-runtime
    VERSION 0.1.0
    DESCRIPTION "MRR Runtime Library"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_library(mrr-runtime STATIC
    src/memory/allocator.cpp
    src/kernel/syscall.cpp
    src/crypto/aes.cpp
    src/net/socket.cpp
)

target_include_directories(mrr-runtime PUBLIC include)

if(WIN32)
    target_link_libraries(mrr-runtime PUBLIC ws2_32 bcrypt ntdll)
endif()

install(TARGETS mrr-runtime DESTINATION lib)
