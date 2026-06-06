/*
 * MRR Compiler — Lexer Interface
 *
 * The Lexer (Lexical Analyzer) transforms MRR source text into a stream
 * of tokens. It handles:
 *   - UTF-8 source input
 *   - Keyword recognition
 *   - Numeric literals (decimal, hex, binary, octal, float)
 *   - String and character literals (with escape sequences)
 *   - Byte string and raw string literals
 *   - Operators and delimiters
 *   - Comments (line, block, doc)
 *   - Source location tracking for error reporting
 */

#pragma once

#include "mrr/lexer/token.h"
#include <string>
#include <vector>
#include <string_view>
#include <functional>

namespace mrr {

// ─── Diagnostic Severity ───
enum class DiagSeverity {
    Note,
    Warning,
    Error,
    Fatal
};

// ─── Diagnostic Message ───
struct Diagnostic {
    DiagSeverity   severity;
    SourceLocation location;
    std::string    message;
};

// ─── Lexer ───
class Lexer {
public:
    /// Construct lexer from source text and file name
    explicit Lexer(std::string source, std::string filename = "<stdin>");

    /// Lex the next token from the source
    Token nextToken();

    /// Peek at the next token without consuming it
    Token peekToken();

    /// Lex all tokens at once (for debugging / testing)
    std::vector<Token> lexAll();

    /// Check if we've reached the end of source
    [[nodiscard]] bool isAtEnd() const;

    /// Get accumulated diagnostics
    [[nodiscard]] const std::vector<Diagnostic>& getDiagnostics() const;

    /// Check if any error diagnostics were emitted
    [[nodiscard]] bool hasErrors() const;

    /// Set diagnostic callback for real-time reporting
    using DiagCallback = std::function<void(const Diagnostic&)>;
    void setDiagCallback(DiagCallback callback);

private:
    std::string    m_source;
    std::string    m_filename;
    size_t         m_pos    = 0;
    uint32_t       m_line   = 1;
    uint32_t       m_column = 1;

    std::vector<Diagnostic> m_diagnostics;
    DiagCallback            m_diagCallback;
    Token                   m_peeked;
    bool                    m_hasPeeked = false;

    // ── Character scanning ──
    char        peek() const;
    char        peekNext() const;
    char        advance();
    bool        match(char expected);
    void        skipWhitespace();
    void        skipLineComment();
    void        skipBlockComment();

    // ── Token constructors ──
    Token       makeToken(TokenKind kind, const std::string& lexeme,
                          const SourceLocation& loc);
    Token       makeError(const std::string& message,
                          const SourceLocation& loc);

    // ── Lexing subroutines ──
    Token       lexIdentifierOrKeyword();
    Token       lexNumber();
    Token       lexString();
    Token       lexChar();
    Token       lexRawString();
    Token       lexByteString();
    Token       lexOperatorOrDelimiter();

    // ── Helpers ──
    SourceLocation currentLocation() const;
    void           emitDiag(DiagSeverity severity,
                            const SourceLocation& loc,
                            const std::string& msg);
    bool           isDigit(char c) const;
    bool           isHexDigit(char c) const;
    bool           isAlpha(char c) const;
    bool           isAlphaNumeric(char c) const;
    char           processEscapeSequence();
};

} // namespace mrr
