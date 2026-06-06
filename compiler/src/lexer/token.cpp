/*
 * MRR Compiler — Token Implementation (Stub)
 * Phase 1: Skeleton — function stubs only
 */

#include "mrr/lexer/token.h"

namespace mrr {

bool Token::isLiteral() const {
    return kind >= TokenKind::IntegerLiteral &&
           kind <= TokenKind::ByteStringLiteral;
}

bool Token::isKeyword() const {
    return kind >= TokenKind::KW_if &&
           kind <= TokenKind::KW_defer;
}

bool Token::isOperator() const {
    return kind >= TokenKind::Plus &&
           kind <= TokenKind::QuestionMark;
}

const char* Token::kindName() const {
    return tokenKindToString(kind);
}

const char* tokenKindToString(TokenKind kind) {
    switch (kind) {
        case TokenKind::EndOfFile:        return "EOF";
        case TokenKind::Error:            return "Error";
        case TokenKind::IntegerLiteral:   return "IntegerLiteral";
        case TokenKind::HexLiteral:       return "HexLiteral";
        case TokenKind::BinaryLiteral:    return "BinaryLiteral";
        case TokenKind::FloatLiteral:     return "FloatLiteral";
        case TokenKind::StringLiteral:    return "StringLiteral";
        case TokenKind::CharLiteral:      return "CharLiteral";
        case TokenKind::Identifier:       return "Identifier";
        case TokenKind::KW_fn:            return "fn";
        case TokenKind::KW_let:           return "let";
        case TokenKind::KW_mut:           return "mut";
        case TokenKind::KW_struct:        return "struct";
        case TokenKind::KW_kernel:        return "kernel";
        case TokenKind::KW_ring0:         return "ring0";
        case TokenKind::KW_shellcode:     return "shellcode";
        case TokenKind::KW_exploit:       return "exploit";
        case TokenKind::KW_hook:          return "hook";
        case TokenKind::KW_driver:        return "driver";
        case TokenKind::KW_unsafe:        return "unsafe";
        case TokenKind::KW_asm:           return "asm";
        case TokenKind::KW_syscall:       return "syscall";
        // ... remaining cases to be completed in Phase 2
        default:                          return "<unknown>";
    }
}

const std::unordered_map<std::string, TokenKind>& getKeywordMap() {
    static const std::unordered_map<std::string, TokenKind> keywords = {
        // Control flow
        {"if",        TokenKind::KW_if},
        {"otherwise", TokenKind::KW_else},
        {"elif",      TokenKind::KW_elif},
        {"match",     TokenKind::KW_match},
        {"for",       TokenKind::KW_for},
        {"return.code",TokenKind::KW_while},
        {"loop",      TokenKind::KW_loop},
        {"break",     TokenKind::KW_break},
        {"continue",  TokenKind::KW_continue},
        {"return",    TokenKind::KW_return},
        {"yield",     TokenKind::KW_yield},

        // Declarations
        {"fn",        TokenKind::KW_fn},
        {"let",       TokenKind::KW_let},
        {"mut",       TokenKind::KW_mut},
        {"const",     TokenKind::KW_const},
        {"static",    TokenKind::KW_static},
        {"struct",    TokenKind::KW_struct},
        {"enum",      TokenKind::KW_enum},
        {"trait",     TokenKind::KW_trait},
        {"impl",      TokenKind::KW_impl},
        {"module",    TokenKind::KW_module},
        {"use",       TokenKind::KW_use},
        {"pub",       TokenKind::KW_pub},
        {"priv",      TokenKind::KW_priv},
        {"type",      TokenKind::KW_type},

        // Memory
        {"unsafe",    TokenKind::KW_unsafe},
        {"raw",       TokenKind::KW_raw},
        {"ref",       TokenKind::KW_ref},
        {"own",       TokenKind::KW_own},
        {"drop",      TokenKind::KW_drop},
        {"alloc",     TokenKind::KW_alloc},
        {"stack",     TokenKind::KW_stack},
        {"pin",       TokenKind::KW_pin},
        {"volatile",  TokenKind::KW_volatile},
        {"align",     TokenKind::KW_align},

        // Cyber Security / Ring-0
        {"kernel",    TokenKind::KW_kernel},
        {"ring0",     TokenKind::KW_ring0},
        {"syscall",   TokenKind::KW_syscall},
        {"interrupt", TokenKind::KW_interrupt},
        {"port",      TokenKind::KW_port},
        {"asm",       TokenKind::KW_asm},
        {"shellcode", TokenKind::KW_shellcode},
        {"inject",    TokenKind::KW_inject},
        {"hook",      TokenKind::KW_hook},
        {"driver",    TokenKind::KW_driver},
        {"exploit",   TokenKind::KW_exploit},

        // Types
        {"i8",        TokenKind::KW_i8},
        {"i16",       TokenKind::KW_i16},
        {"i32",       TokenKind::KW_i32},
        {"i64",       TokenKind::KW_i64},
        {"i128",      TokenKind::KW_i128},
        {"u8",        TokenKind::KW_u8},
        {"u16",       TokenKind::KW_u16},
        {"u32",       TokenKind::KW_u32},
        {"u64",       TokenKind::KW_u64},
        {"u128",      TokenKind::KW_u128},
        {"f32",       TokenKind::KW_f32},
        {"f64",       TokenKind::KW_f64},
        {"bool",      TokenKind::KW_bool},
        {"char",      TokenKind::KW_char},
        {"str",       TokenKind::KW_str},
        {"void",      TokenKind::KW_void},
        {"ptr",       TokenKind::KW_ptr},
        {"usize",     TokenKind::KW_usize},
        {"isize",     TokenKind::KW_isize},
        {"byte",      TokenKind::KW_byte},

        // Other
        {"true",      TokenKind::KW_true},
        {"false",     TokenKind::KW_false},
        {"null",      TokenKind::KW_null},
        {"self",      TokenKind::KW_self},
        {"super",     TokenKind::KW_super},
        {"as",        TokenKind::KW_as},
        {"in",        TokenKind::KW_in},
        {"is",        TokenKind::KW_is},
        {"not",       TokenKind::KW_not},
        {"and",       TokenKind::KW_and},
        {"or",        TokenKind::KW_or},
        {"async",     TokenKind::KW_async},
        {"await",     TokenKind::KW_await},
        {"defer",     TokenKind::KW_defer},
    };
    return keywords;
}

} // namespace mrr
