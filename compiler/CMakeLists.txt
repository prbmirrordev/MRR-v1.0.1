cmake_minimum_required(VERSION 3.20)
project(mrr-compiler
    VERSION 0.1.0
    DESCRIPTION "MRR Programming Language Compiler"
    LANGUAGES CXX
)

# ─── C++20 Standard ───
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

# ─── Compiler Flags ───
if(MSVC)
    add_compile_options(/W4 /WX /permissive- /Zc:preprocessor)
    add_compile_definitions(_CRT_SECURE_NO_WARNINGS)
else()
    add_compile_options(-Wall -Wextra -Wpedantic -Werror)
endif()

# ─── Output Directories ───
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
set(CMAKE_LIBRARY_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)
set(CMAKE_ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib)

# ─── Include Paths ───
include_directories(
    ${CMAKE_SOURCE_DIR}/include
    ${CMAKE_SOURCE_DIR}/src
)

# ─── Source Files ───
# Lexer
set(LEXER_SOURCES
    src/lexer/token.cpp
    src/lexer/lexer.cpp
)

# Parser
set(PARSER_SOURCES
    src/parser/ast.cpp
    src/parser/parser.cpp
)

# Semantic Analysis
set(SEMA_SOURCES
    src/sema/type_checker.cpp
    src/sema/symbol_table.cpp
)

# Intermediate Representation
set(IR_SOURCES
    src/ir/ir_builder.cpp
    src/ir/ir_node.cpp
)

# Code Generator
set(CODEGEN_SOURCES
    src/codegen/x86_64_emitter.cpp
    src/codegen/codegen.cpp
)

# Driver
set(DRIVER_SOURCES
    src/driver/main.cpp
    src/driver/cli.cpp
)

# ─── Compiler Library ───
add_library(mrr-core STATIC
    ${LEXER_SOURCES}
    ${PARSER_SOURCES}
    ${SEMA_SOURCES}
    ${IR_SOURCES}
    ${CODEGEN_SOURCES}
)
target_include_directories(mrr-core PUBLIC include)

# ─── Compiler Executable ───
add_executable(mrrc ${DRIVER_SOURCES})
target_link_libraries(mrrc PRIVATE mrr-core)

# ─── Tests ───
option(MRR_BUILD_TESTS "Build MRR compiler tests" ON)
if(MRR_BUILD_TESTS)
    enable_testing()
    add_subdirectory(tests)
endif()

# ─── Install ───
install(TARGETS mrrc DESTINATION bin)
install(TARGETS mrr-core DESTINATION lib)
install(DIRECTORY include/ DESTINATION include)

message(STATUS "")
message(STATUS "╔══════════════════════════════════════╗")
message(STATUS "║   MRR Compiler v${PROJECT_VERSION}              ║")
message(STATUS "║   Build Type: ${CMAKE_BUILD_TYPE}                 ║")
message(STATUS "║   C++ Standard: C++${CMAKE_CXX_STANDARD}              ║")
message(STATUS "╚══════════════════════════════════════╝")
message(STATUS "")
