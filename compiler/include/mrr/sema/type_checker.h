/*
 * MRR Compiler — Semantic Analysis Interface
 */

#pragma once

#include "mrr/parser/ast.h"
#include "mrr/sema/symbol_table.h"
#include <memory>

namespace mrr {

class TypeChecker {
public:
    TypeChecker();

    /// Run semantic analysis on a parsed program
    bool analyze(ast::Program& program);

    /// Get diagnostics from analysis
    [[nodiscard]] const std::vector<Diagnostic>& getDiagnostics() const;

private:
    SymbolTable             m_symbols;
    std::vector<Diagnostic> m_diagnostics;

    void checkDeclaration(ast::Declaration& decl);
    void checkStatement(ast::Statement& stmt);
    void checkExpression(ast::Expression& expr);

    void checkFunctionDecl(ast::FunctionDecl& fn);
    void checkStructDecl(ast::StructDecl& s);
    void checkDriverDecl(ast::DriverDecl& d);
    void checkExploitDecl(ast::ExploitDecl& e);

    void checkUnsafeContext(ast::ASTNode& node, const std::string& operation);
    bool isTypeCompatible(const ast::TypeRef& from, const ast::TypeRef& to);

    void error(const SourceLocation& loc, const std::string& msg);
};

} // namespace mrr
