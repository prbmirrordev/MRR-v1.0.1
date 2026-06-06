/*
 * MRR Compiler — Token Definitions
 * 
 * Defines all token types recognized by the MRR lexer.
 * Token categories:
 *   - Literals (integers, floats, strings, hex, binary)
 *   - Keywords (language keywords including cyber-security primitives)
 *   - Operators (arithmetic, bitwise, logical, pointer)
 *   - Delimiters (braces, brackets, semicolons)
 *   - Identifiers
 */

#pragma once

#include <string>
#include <cstdint>
#include <unordered_map>

namespace mrr {

// ─── Source Location ───
struct SourceLocation {
    std::string file;
    uint32_t    line   = 1;
    uint32_t    column = 1;
    uint32_t    offset = 0;
};

// ─── Token Kind ───
enum class TokenKind : uint16_t {
    // ── End / Error ──
    EndOfFile = 0,
    Error,

    // ── Literals ──
    IntegerLiteral,       // 42
    HexLiteral,           // 0xFF
    BinaryLiteral,        // 0b1010
    OctalLiteral,         // 0o77
    FloatLiteral,         // 3.14
    StringLiteral,        // "hello"
    CharLiteral,          // 'c'
    RawStringLiteral,     // r"raw\nstring"
    ByteStringLiteral,    // b"\x41\x42"

    // ── Identifiers ──
    Identifier,           // variable_name
    TypeIdentifier,       // PascalCase type name
    MacroIdentifier,      // @macro_name

    // ── Keywords: Control Flow ──
    KW_if,
    KW_else,
    KW_elif,
    KW_match,
    KW_for,
    KW_while,
    KW_loop,
    KW_break,
    KW_continue,
    KW_return,
    KW_yield,

    // ── Keywords: Declarations ──
    KW_fn,                // Function declaration
    KW_let,               // Immutable binding
    KW_mut,               // Mutable binding
    KW_const,             // Compile-time constant
    KW_static,            // Static storage
    KW_struct,            // Struct definition
    KW_enum,              // Enum definition
    KW_trait,             // Trait (interface) definition
    KW_impl,              // Implementation block
    KW_module,            // Module declaration
    KW_use,               // Import / use
    KW_pub,               // Public visibility
    KW_priv,              // Private visibility
    KW_type,              // Type alias

    // ── Keywords: Memory & Pointers ──
    KW_unsafe,            // Unsafe block
    KW_raw,               // Raw pointer
    KW_ref,               // Reference
    KW_own,               // Ownership transfer
    KW_drop,              // Manual deallocation
    KW_alloc,             // Heap allocation
    KW_stack,             // Stack allocation
    KW_pin,               // Pin memory (prevent move)
    KW_volatile,          // Volatile memory access
    KW_align,             // Memory alignment

    // ── Keywords: Cyber Security / Ring-0 ──
    KW_kernel,            // Kernel-mode block
    KW_ring0,             // Ring-0 context
    KW_syscall,           // System call
    KW_interrupt,         // Interrupt handler
    KW_port,              // I/O port access
    KW_asm,               // Inline assembly
    KW_shellcode,         // Shellcode block
    KW_inject,            // Process injection
    KW_hook,              // Function hooking
    KW_driver,            // Driver entry point
    KW_exploit,           // Exploit module marker

    // ── Keywords: Types ──
    KW_i8,
    KW_i16,
    KW_i32,
    KW_i64,
    KW_i128,
    KW_u8,
    KW_u16,
    KW_u32,
    KW_u64,
    KW_u128,
    KW_f32,
    KW_f64,
    KW_bool,
    KW_char,
    KW_str,
    KW_void,
    KW_ptr,               // Generic pointer type
    KW_usize,
    KW_isize,
    KW_byte,              // Alias for u8

    // ── Keywords: Other ──
    KW_true,
    KW_false,
    KW_null,
    KW_self,
    KW_super,
    KW_as,
    KW_in,
    KW_is,
    KW_not,
    KW_and,
    KW_or,
    KW_async,
    KW_await,
    KW_defer,

    // ── Operators: Arithmetic ──
    Plus,                 // +
    Minus,                // -
    Star,                 // *
    Slash,                // /
    Percent,              // %
    DoubleStar,           // ** (power)

    // ── Operators: Bitwise ──
    Ampersand,            // &
    Pipe,                 // |
    Caret,                // ^
    Tilde,                // ~
    ShiftLeft,            // <<
    ShiftRight,           // >>

    // ── Operators: Comparison ──
    Equal,                // ==
    NotEqual,             // !=
    Less,                 // <
    Greater,              // >
    LessEqual,            // <=
    GreaterEqual,         // >=

    // ── Operators: Assignment ──
    Assign,               // =
    PlusAssign,           // +=
    MinusAssign,          // -=
    StarAssign,           // *=
    SlashAssign,          // /=
    PercentAssign,        // %=
    AmpersandAssign,      // &=
    PipeAssign,           // |=
    CaretAssign,          // ^=
    ShiftLeftAssign,      // <<=
    ShiftRightAssign,     // >>=

    // ── Operators: Pointer / Reference ──
    Arrow,                // ->
    FatArrow,             // =>
    DoubleColon,          // ::
    Dot,                  // .
    DotDot,               // ..
    DotDotDot,            // ...
    At,                   // @ (macro / decorator)
    Hash,                 // # (attribute)

    // ── Operators: Logical ──
    LogicalAnd,           // &&
    LogicalOr,            // ||
    Bang,                 // !
    QuestionMark,         // ?

    // ── Delimiters ──
    LeftParen,            // (
    RightParen,           // )
    LeftBrace,            // {
    RightBrace,           // }
    LeftBracket,          // [
    RightBracket,         // ]
    Semicolon,            // ;
    Colon,                // :
    Comma,                // ,

    // ── Special ──
    Newline,              // Significant newline (Ruby-style)
    Comment,              // // or /* */
    DocComment,           // /// or /** */

    _TOKEN_COUNT
};

// ─── Token ───
struct Token {
    TokenKind      kind     = TokenKind::Error;
    std::string    lexeme;
    SourceLocation location;

    // Literal value storage
    union {
        int64_t    int_val;
        uint64_t   uint_val;
        double     float_val;
        bool       bool_val;
    } value = {};

    [[nodiscard]] bool is(TokenKind k) const { return kind == k; }
    [[nodiscard]] bool isNot(TokenKind k) const { return kind != k; }
    [[nodiscard]] bool isLiteral() const;
    [[nodiscard]] bool isKeyword() const;
    [[nodiscard]] bool isOperator() const;
    [[nodiscard]] const char* kindName() const;
};

// ─── Keyword Lookup ───
const std::unordered_map<std::string, TokenKind>& getKeywordMap();

// ─── Token Kind Name ───
const char* tokenKindToString(TokenKind kind);

} // namespace mrr
