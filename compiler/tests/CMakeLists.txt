cmake_minimum_required(VERSION 3.20)

# MRR Compiler Tests
# TODO: Add Google Test or Catch2 in Phase 2

add_executable(mrr_tests
    test_lexer.cpp
    test_parser.cpp
)

target_link_libraries(mrr_tests PRIVATE mrr-core)

add_test(NAME MRRTests COMMAND mrr_tests)
