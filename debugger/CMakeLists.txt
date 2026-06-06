cmake_minimum_required(VERSION 3.20)
project(mrr-debugger
    VERSION 0.1.0
    DESCRIPTION "MRR Debugger — Debug Adapter Protocol Server"
    LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

include_directories(include)

# ─── Debugger Library ───
add_library(mrr-debug STATIC
    src/dap/dap_server.cpp
    src/core/debug_core.cpp
    src/bridge/kernel_bridge.cpp
)

# ─── Debugger Executable ───
add_executable(mrr-dbg src/main.cpp)
target_link_libraries(mrr-dbg PRIVATE mrr-debug)

# Platform-specific linking
if(WIN32)
    target_link_libraries(mrr-debug PUBLIC dbghelp)
endif()

install(TARGETS mrr-dbg DESTINATION bin)

message(STATUS "MRR Debugger v${PROJECT_VERSION}")
