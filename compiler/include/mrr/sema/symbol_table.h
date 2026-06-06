/*
 * MRR Compiler — Symbol Table
 */

#pragma once

#include "mrr/parser/ast.h"
#include <string>
#include <unordered_map>
#include <vector>
#include <optional>

namespace mrr {

enum class SymbolKind {
    Variable,
    Function,
    Type,
    Module,
    Trait,
    Field,
    Parameter
};

struct Symbol {
    std::string    name;
    SymbolKind     kind;
    ast::TypeRef   type;
    bool           is_mutable  = false;
    bool           is_public   = false;
    bool           is_unsafe   = false;
    SourceLocation defined_at;
};

class SymbolTable {
public:
    SymbolTable();

    /// Push a new scope (entering block / function / module)
    void pushScope();

    /// Pop the current scope
    void popScope();

    /// Define a symbol in the current scope
    bool define(const Symbol& symbol);

    /// Look up a symbol (searches outward from current scope)
    std::optional<Symbol> lookup(const std::string& name) const;

    /// Look up only in the current (innermost) scope
    std::optional<Symbol> lookupLocal(const std::string& name) const;

    /// Get current scope depth
    [[nodiscard]] size_t depth() const;

private:
    using Scope = std::unordered_map<std::string, Symbol>;
    std::vector<Scope> m_scopes;
};

} // namespace mrr
