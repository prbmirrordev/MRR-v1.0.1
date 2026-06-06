/*
 * MRR Compiler — Semantic Analysis: Type Checker (Stub)
 * Phase 1: Skeleton
 */

#include "mrr/sema/type_checker.h"

namespace mrr {

TypeChecker::TypeChecker() {}

bool TypeChecker::analyze(ast::Program& program) {
    m_symbols.pushScope(); // Global scope

    for (auto& decl : program.declarations) {
        if (decl) checkDeclaration(*decl);
    }

    m_symbols.popScope();
    return m_diagnostics.empty();
}

const std::vector<Diagnostic>& TypeChecker::getDiagnostics() const {
    return m_diagnostics;
}

// ── Stubs (Phase 2) ──
void TypeChecker::checkDeclaration(ast::Declaration&) {}
void TypeChecker::checkStatement(ast::Statement&) {}
void TypeChecker::checkExpression(ast::Expression&) {}
void TypeChecker::checkFunctionDecl(ast::FunctionDecl&) {}
void TypeChecker::checkStructDecl(ast::StructDecl&) {}
void TypeChecker::checkDriverDecl(ast::DriverDecl&) {}
void TypeChecker::checkExploitDecl(ast::ExploitDecl&) {}
void TypeChecker::checkUnsafeContext(ast::ASTNode&, const std::string&) {}
bool TypeChecker::isTypeCompatible(const ast::TypeRef&, const ast::TypeRef&) { return true; }

void TypeChecker::error(const SourceLocation& loc, const std::string& msg) {
    m_diagnostics.push_back({DiagSeverity::Error, loc, msg});
}

} // namespace mrr
