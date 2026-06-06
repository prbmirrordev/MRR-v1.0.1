/*
 * MRR Compiler — Parser Interface
 *
 * Recursive descent parser that transforms a token stream into an AST.
 * Supports:
 *   - Standard expressions with operator precedence
 *   - Control flow (if/elif/else, match, for, while, loop)
 *   - Function / struct / enum / trait / impl declarations
 *   - Unsafe blocks and raw pointer operations
 *   - Cyber-security constructs (kernel, driver, exploit, hook, shellcode, asm)
 */

#pragma once

#include "mrr/lexer/lexer.h"
#include "mrr/parser/ast.h"
#include <memory>
#include <vector>

namespace mrr {

class Parser {
public:
    explicit Parser(Lexer& lexer);

    /// Parse the entire source into a Program AST
    std::unique_ptr<ast::Program> parseProgram();

    /// Get accumulated parse diagnostics
    [[nodiscard]] const std::vector<Diagnostic>& getDiagnostics() const;
    [[nodiscard]] bool hasErrors() const;

private:
    Lexer&                  m_lexer;
    Token                   m_current;
    Token                   m_previous;
    std::vector<Diagnostic> m_diagnostics;
    bool                    m_hadError  = false;
    bool                    m_panicMode = false;

    // ── Token consumption ──
    Token   advance();
    Token   consume(TokenKind kind, const std::string& message);
    bool    check(TokenKind kind) const;
    bool    match(TokenKind kind);
    bool    matchAny(std::initializer_list<TokenKind> kinds);

    // ── Error handling ──
    void    error(const std::string& message);
    void    errorAt(const Token& token, const std::string& message);
    void    synchronize();

    // ── Declarations ──
    ast::DeclPtr  parseDeclaration();
    ast::DeclPtr  parseFunctionDecl(bool is_pub);
    ast::DeclPtr  parseStructDecl(bool is_pub);
    ast::DeclPtr  parseEnumDecl(bool is_pub);
    ast::DeclPtr  parseTraitDecl(bool is_pub);
    ast::DeclPtr  parseImplDecl();
    ast::DeclPtr  parseModuleDecl();
    ast::DeclPtr  parseUseDecl();
    ast::DeclPtr  parseDriverDecl();
    ast::DeclPtr  parseExploitDecl();
    ast::DeclPtr  parseHookDecl();
    ast::DeclPtr  parseInterruptDecl();

    // ── Statements ──
    ast::StmtPtr  parseStatement();
    ast::StmtPtr  parseVarDecl();
    ast::StmtPtr  parseBlock();
    ast::StmtPtr  parseIfStmt();
    ast::StmtPtr  parseMatchStmt();
    ast::StmtPtr  parseForStmt();
    ast::StmtPtr  parseWhileStmt();
    ast::StmtPtr  parseLoopStmt();
    ast::StmtPtr  parseReturnStmt();
    ast::StmtPtr  parseUnsafeBlock();
    ast::StmtPtr  parseDeferStmt();
    ast::StmtPtr  parseExprStmt();

    // ── Expressions (Pratt parsing / precedence climbing) ──
    ast::ExprPtr  parseExpression();
    ast::ExprPtr  parsePrecedence(int minPrec);
    ast::ExprPtr  parsePrimary();
    ast::ExprPtr  parseUnary();
    ast::ExprPtr  parseBinary(ast::ExprPtr left, int prec);
    ast::ExprPtr  parseCall(ast::ExprPtr callee);
    ast::ExprPtr  parseMemberAccess(ast::ExprPtr object);
    ast::ExprPtr  parseIndex(ast::ExprPtr object);
    ast::ExprPtr  parseCast(ast::ExprPtr operand);
    ast::ExprPtr  parseLiteral();
    ast::ExprPtr  parseIdentifier();
    ast::ExprPtr  parseGrouping();
    ast::ExprPtr  parseAsmExpr();
    ast::ExprPtr  parseSyscallExpr();
    ast::ExprPtr  parseShellcodeExpr();
    ast::ExprPtr  parseLambda();

    // ── Types ──
    ast::TypeRef  parseType();
    ast::FnParam  parseParam();
    std::vector<ast::FnParam> parseParamList();

    // ── Helpers ──
    int  getOperatorPrecedence(TokenKind kind) const;
    bool isAtEnd() const;
};

} // namespace mrr
