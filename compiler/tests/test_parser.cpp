/*
 * MRR Compiler — Parser Tests (Stub)
 * Phase 1: Skeleton test structure
 */

#include "mrr/lexer/lexer.h"
#include "mrr/parser/parser.h"
#include <iostream>
#include <cassert>

void test_empty_program() {
    mrr::Lexer lexer("", "test");
    mrr::Parser parser(lexer);
    auto program = parser.parseProgram();
    assert(program != nullptr);
    assert(program->declarations.empty());
    std::cout << "[PASS] test_empty_program\n";
}

int main() {
    std::cout << "═══ MRR Parser Tests ═══\n";
    test_empty_program();
    std::cout << "═══ All parser tests passed ═══\n";
    return 0;
}
