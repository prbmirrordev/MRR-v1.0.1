/*
 * MRR Compiler — Parser Implementation (Stub)
 * Phase 1: Skeleton — structural framework, full parsing in Phase 2
 */

#include "mrr/parser/parser.h"
#include <iostream>

namespace mrr {

Parser::Parser(Lexer& lexer)
    : m_lexer(lexer)
{
    m_current = m_lexer.nextToken();
}

std::unique_ptr<ast::Program> Parser::parseProgram() {
    auto program = std::make_unique<ast::Program>();

    while (!isAtEnd()) {
        auto decl = parseDeclaration();
        if (decl) {
            program->declarations.push_back(std::move(decl));
        }
    }

    program->diagnostics.insert(
        program->diagnostics.end(),
        m_diagnostics.begin(),
        m_diagnostics.end()
    );

    return program;
}

const std::vector<Diagnostic>& Parser::getDiagnostics() const {
    return m_diagnostics;
}

bool Parser::hasErrors() const {
    return m_hadError;
}

// ── Token consumption ──

Token Parser::advance() {
    m_previous = m_current;
    m_current = m_lexer.nextToken();
    return m_previous;
}

Token Parser::consume(TokenKind kind, const std::string& message) {
    if (check(kind)) return advance();
    errorAt(m_current, message);
    return m_current;
}

bool Parser::check(TokenKind kind) const {
    return m_current.is(kind);
}

bool Parser::match(TokenKind kind) {
    if (!check(kind)) return false;
    advance();
    return true;
}

bool Parser::matchAny(std::initializer_list<TokenKind> kinds) {
    for (auto k : kinds) {
        if (match(k)) return true;
    }
    return false;
}

// ── Error handling ──

void Parser::error(const std::string& message) {
    errorAt(m_current, message);
}

void Parser::errorAt(const Token& token, const std::string& message) {
    if (m_panicMode) return;
    m_panicMode = true;
    m_hadError = true;

    Diagnostic d;
    d.severity = DiagSeverity::Error;
    d.location = token.location;
    d.message = message;
    m_diagnostics.push_back(d);
}

void Parser::synchronize() {
    m_panicMode = false;
    while (!isAtEnd()) {
        if (m_previous.is(TokenKind::Semicolon)) return;
        switch (m_current.kind) {
            case TokenKind::KW_fn:
            case TokenKind::KW_struct:
            case TokenKind::KW_enum:
            case TokenKind::KW_trait:
            case TokenKind::KW_impl:
            case TokenKind::KW_let:
            case TokenKind::KW_mut:
            case TokenKind::KW_if:
            case TokenKind::KW_for:
            case TokenKind::KW_while:
            case TokenKind::KW_return:
            case TokenKind::KW_driver:
            case TokenKind::KW_exploit:
            case TokenKind::KW_hook:
            case TokenKind::KW_kernel:
                return;
            default:
                advance();
        }
    }
}

bool Parser::isAtEnd() const {
    return m_current.is(TokenKind::EndOfFile);
}

// ── Declarations (Stubs — Phase 2) ──

ast::DeclPtr Parser::parseDeclaration() {
    // TODO: Phase 2 — dispatch based on current token
    error("Declaration parsing not yet implemented");
    advance();
    return nullptr;
}

ast::DeclPtr Parser::parseFunctionDecl(bool) { return nullptr; }
ast::DeclPtr Parser::parseStructDecl(bool) { return nullptr; }
ast::DeclPtr Parser::parseEnumDecl(bool) { return nullptr; }
ast::DeclPtr Parser::parseTraitDecl(bool) { return nullptr; }
ast::DeclPtr Parser::parseImplDecl() { return nullptr; }
ast::DeclPtr Parser::parseModuleDecl() { return nullptr; }
ast::DeclPtr Parser::parseUseDecl() { return nullptr; }
ast::DeclPtr Parser::parseDriverDecl() { return nullptr; }
ast::DeclPtr Parser::parseExploitDecl() { return nullptr; }
ast::DeclPtr Parser::parseHookDecl() { return nullptr; }
ast::DeclPtr Parser::parseInterruptDecl() { return nullptr; }

// ── Statements (Stubs — Phase 2) ──

ast::StmtPtr Parser::parseStatement() { return nullptr; }
ast::StmtPtr Parser::parseVarDecl() { return nullptr; }
ast::StmtPtr Parser::parseBlock() { return nullptr; }
ast::StmtPtr Parser::parseIfStmt() { return nullptr; }
ast::StmtPtr Parser::parseMatchStmt() { return nullptr; }
ast::StmtPtr Parser::parseForStmt() { return nullptr; }
ast::StmtPtr Parser::parseWhileStmt() { return nullptr; }
ast::StmtPtr Parser::parseLoopStmt() { return nullptr; }
ast::StmtPtr Parser::parseReturnStmt() { return nullptr; }
ast::StmtPtr Parser::parseUnsafeBlock() { return nullptr; }
ast::StmtPtr Parser::parseDeferStmt() { return nullptr; }
ast::StmtPtr Parser::parseExprStmt() { return nullptr; }

// ── Expressions (Stubs — Phase 2) ──

ast::ExprPtr Parser::parseExpression() { return nullptr; }
ast::ExprPtr Parser::parsePrecedence(int) { return nullptr; }
ast::ExprPtr Parser::parsePrimary() { return nullptr; }
ast::ExprPtr Parser::parseUnary() { return nullptr; }
ast::ExprPtr Parser::parseBinary(ast::ExprPtr, int) { return nullptr; }
ast::ExprPtr Parser::parseCall(ast::ExprPtr) { return nullptr; }
ast::ExprPtr Parser::parseMemberAccess(ast::ExprPtr) { return nullptr; }
ast::ExprPtr Parser::parseIndex(ast::ExprPtr) { return nullptr; }
ast::ExprPtr Parser::parseCast(ast::ExprPtr) { return nullptr; }
ast::ExprPtr Parser::parseLiteral() { return nullptr; }
ast::ExprPtr Parser::parseIdentifier() { return nullptr; }
ast::ExprPtr Parser::parseGrouping() { return nullptr; }
ast::ExprPtr Parser::parseAsmExpr() { return nullptr; }
ast::ExprPtr Parser::parseSyscallExpr() { return nullptr; }
ast::ExprPtr Parser::parseShellcodeExpr() { return nullptr; }
ast::ExprPtr Parser::parseLambda() { return nullptr; }

// ── Types (Stubs — Phase 2) ──

ast::TypeRef Parser::parseType() { return ast::TypeRef{}; }
ast::FnParam Parser::parseParam() { return ast::FnParam{}; }
std::vector<ast::FnParam> Parser::parseParamList() { return {}; }

int Parser::getOperatorPrecedence(TokenKind) const { return -1; }

} // namespace mrr
