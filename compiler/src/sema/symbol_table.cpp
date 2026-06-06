/*
 * MRR Compiler — Symbol Table Implementation
 * Phase 1: Fully functional — used by sema layer
 */

#include "mrr/sema/symbol_table.h"

namespace mrr {

SymbolTable::SymbolTable() {
    // Start with global scope
    m_scopes.emplace_back();
}

void SymbolTable::pushScope() {
    m_scopes.emplace_back();
}

void SymbolTable::popScope() {
    if (m_scopes.size() > 1) {
        m_scopes.pop_back();
    }
}

bool SymbolTable::define(const Symbol& symbol) {
    auto& current = m_scopes.back();
    if (current.count(symbol.name)) {
        return false; // Already defined in current scope
    }
    current[symbol.name] = symbol;
    return true;
}

std::optional<Symbol> SymbolTable::lookup(const std::string& name) const {
    // Search from innermost to outermost scope
    for (auto it = m_scopes.rbegin(); it != m_scopes.rend(); ++it) {
        auto found = it->find(name);
        if (found != it->end()) {
            return found->second;
        }
    }
    return std::nullopt;
}

std::optional<Symbol> SymbolTable::lookupLocal(const std::string& name) const {
    auto& current = m_scopes.back();
    auto found = current.find(name);
    if (found != current.end()) {
        return found->second;
    }
    return std::nullopt;
}

size_t SymbolTable::depth() const {
    return m_scopes.size();
}

} // namespace mrr
