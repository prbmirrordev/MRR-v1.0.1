/*
 * MRR Compiler — IR Builder (Stub)
 * Phase 1: Skeleton
 */

#include "mrr/ir/ir_builder.h"

namespace mrr {

IRBuilder::IRBuilder() {}

std::unique_ptr<ir::IRModule> IRBuilder::lower(const ast::Program& program) {
    auto module = std::make_unique<ir::IRModule>();
    m_module = module.get();
    module->name = program.module_name;

    for (const auto& decl : program.declarations) {
        if (decl) lowerDeclaration(*decl);
    }

    return module;
}

// ── Stubs (Phase 2 / 3) ──
void IRBuilder::lowerDeclaration(const ast::Declaration&) {}
void IRBuilder::lowerFunction(const ast::FunctionDecl&) {}
void IRBuilder::lowerStatement(const ast::Statement&) {}
uint32_t IRBuilder::lowerExpression(const ast::Expression&) { return 0; }

uint32_t IRBuilder::newReg() { return m_nextReg++; }

ir::BasicBlock& IRBuilder::newBlock(const std::string& label) {
    if (m_func) {
        m_func->blocks.push_back({label, {}, {}, {}});
        return m_func->blocks.back();
    }
    static ir::BasicBlock dummy;
    return dummy;
}

void IRBuilder::emit(ir::IRInst inst) {
    if (m_block) {
        m_block->instructions.push_back(std::move(inst));
    }
}

ir::IRType IRBuilder::astTypeToIR(const ast::TypeRef&) {
    return ir::IRType::I32; // Placeholder
}

} // namespace mrr
