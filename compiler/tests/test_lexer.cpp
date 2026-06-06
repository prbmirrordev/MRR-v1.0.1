/*
 * MRR Compiler — Lexer Tests (Stub)
 * Phase 1: Skeleton test structure
 */

#include "mrr/lexer/lexer.h"
#include <iostream>
#include <cassert>

void test_empty_source() {
    mrr::Lexer lexer("", "test");
    auto token = lexer.nextToken();
    assert(token.is(mrr::TokenKind::EndOfFile));
    std::cout << "[PASS] test_empty_source\n";
}

void test_whitespace_only() {
    mrr::Lexer lexer("   \t\n  \n  ", "test");
    auto token = lexer.nextToken();
    assert(token.is(mrr::TokenKind::EndOfFile));
    std::cout << "[PASS] test_whitespace_only\n";
}

void test_line_comment() {
    mrr::Lexer lexer("// this is a comment\n", "test");
    auto token = lexer.nextToken();
    assert(token.is(mrr::TokenKind::EndOfFile));
    std::cout << "[PASS] test_line_comment\n";
}

void test_block_comment() {
    mrr::Lexer lexer("/* block comment */", "test");
    auto token = lexer.nextToken();
    assert(token.is(mrr::TokenKind::EndOfFile));
    std::cout << "[PASS] test_block_comment\n";
}

int main() {
    std::cout << "═══ MRR Lexer Tests ═══\n";
    test_empty_source();
    test_whitespace_only();
    test_line_comment();
    test_block_comment();
    std::cout << "═══ All lexer tests passed ═══\n";
    return 0;
}
