/*
 * MRR Compiler — Lexer Implementation (Stub)
 * Phase 1: Skeleton — minimal scaffolding, full implementation in Phase 2
 */

#include "mrr/lexer/lexer.h"
#include <iostream>

namespace mrr {

Lexer::Lexer(std::string source, std::string filename)
    : m_source(std::move(source))
    , m_filename(std::move(filename))
{}

Token Lexer::nextToken() {
    if (m_hasPeeked) {
        m_hasPeeked = false;
        return m_peeked;
    }

    skipWhitespace();

    if (isAtEnd()) {
        return makeToken(TokenKind::EndOfFile, "", currentLocation());
    }

    // Phase 2: Full lexing logic
    // For now, return Error for any character
    auto loc = currentLocation();
    char c = advance();
    return makeError(std::string("Unexpected character: ") + c, loc);
}

Token Lexer::peekToken() {
    if (!m_hasPeeked) {
        m_peeked = nextToken();
        m_hasPeeked = true;
    }
    return m_peeked;
}

std::vector<Token> Lexer::lexAll() {
    std::vector<Token> tokens;
    while (true) {
        auto token = nextToken();
        tokens.push_back(token);
        if (token.is(TokenKind::EndOfFile)) break;
    }
    return tokens;
}

bool Lexer::isAtEnd() const {
    return m_pos >= m_source.size();
}

const std::vector<Diagnostic>& Lexer::getDiagnostics() const {
    return m_diagnostics;
}

bool Lexer::hasErrors() const {
    for (const auto& d : m_diagnostics) {
        if (d.severity == DiagSeverity::Error ||
            d.severity == DiagSeverity::Fatal) return true;
    }
    return false;
}

void Lexer::setDiagCallback(DiagCallback callback) {
    m_diagCallback = std::move(callback);
}

// ── Character scanning ──

char Lexer::peek() const {
    if (isAtEnd()) return '\0';
    return m_source[m_pos];
}

char Lexer::peekNext() const {
    if (m_pos + 1 >= m_source.size()) return '\0';
    return m_source[m_pos + 1];
}

char Lexer::advance() {
    char c = m_source[m_pos++];
    if (c == '\n') {
        m_line++;
        m_column = 1;
    } else {
        m_column++;
    }
    return c;
}

bool Lexer::match(char expected) {
    if (isAtEnd() || m_source[m_pos] != expected) return false;
    advance();
    return true;
}

void Lexer::skipWhitespace() {
    while (!isAtEnd()) {
        char c = peek();
        switch (c) {
            case ' ':
            case '\t':
            case '\r':
                advance();
                break;
            case '\n':
                advance();
                break;
            case '/':
                if (peekNext() == '/') {
                    skipLineComment();
                } else if (peekNext() == '*') {
                    skipBlockComment();
                } else {
                    return;
                }
                break;
            default:
                return;
        }
    }
}

void Lexer::skipLineComment() {
    while (!isAtEnd() && peek() != '\n') advance();
}

void Lexer::skipBlockComment() {
    advance(); // skip /
    advance(); // skip *
    int depth = 1;
    while (!isAtEnd() && depth > 0) {
        if (peek() == '/' && peekNext() == '*') {
            advance(); advance();
            depth++;
        } else if (peek() == '*' && peekNext() == '/') {
            advance(); advance();
            depth--;
        } else {
            advance();
        }
    }
}

// ── Token construction ──

Token Lexer::makeToken(TokenKind kind, const std::string& lexeme,
                       const SourceLocation& loc) {
    Token t;
    t.kind = kind;
    t.lexeme = lexeme;
    t.location = loc;
    return t;
}

Token Lexer::makeError(const std::string& message, const SourceLocation& loc) {
    emitDiag(DiagSeverity::Error, loc, message);
    return makeToken(TokenKind::Error, message, loc);
}

SourceLocation Lexer::currentLocation() const {
    return SourceLocation{m_filename, m_line, m_column,
                          static_cast<uint32_t>(m_pos)};
}

void Lexer::emitDiag(DiagSeverity severity, const SourceLocation& loc,
                     const std::string& msg) {
    Diagnostic d{severity, loc, msg};
    m_diagnostics.push_back(d);
    if (m_diagCallback) m_diagCallback(d);
}

// ── Placeholder lexing subroutines (Phase 2) ──

Token Lexer::lexIdentifierOrKeyword() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexNumber() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexString() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexChar() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexRawString() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexByteString() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

Token Lexer::lexOperatorOrDelimiter() {
    // TODO: Phase 2
    return makeError("Not implemented", currentLocation());
}

bool Lexer::isDigit(char c) const { return c >= '0' && c <= '9'; }
bool Lexer::isHexDigit(char c) const {
    return isDigit(c) || (c >= 'a' && c <= 'f') || (c >= 'A' && c <= 'F');
}
bool Lexer::isAlpha(char c) const {
    return (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || c == '_';
}
bool Lexer::isAlphaNumeric(char c) const { return isAlpha(c) || isDigit(c); }

char Lexer::processEscapeSequence() {
    // TODO: Phase 2
    return '\0';
}

} // namespace mrr
