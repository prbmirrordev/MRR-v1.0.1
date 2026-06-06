/*
 * MRR Compiler — IR Builder Interface
 */

#pragma once

#include "mrr/ir/ir_node.h"
#include "mrr/parser/ast.h"
#include <memory>

namespace mrr {

class IRBuilder {
public:
    IRBuilder();

    /// Lower an AST Program to an IR Module
    std::unique_ptr<ir::IRModule> lower(const ast::Program& program);

private:
    ir::IRModule*    m_module  = nullptr;
    ir::IRFunction*  m_func   = nullptr;
    ir::BasicBlock*  m_block  = nullptr;
    uint32_t         m_nextReg = 0;

    // Lowering functions
    void lowerDeclaration(const ast::Declaration& decl);
    void lowerFunction(const ast::FunctionDecl& fn);
    void lowerStatement(const ast::Statement& stmt);
    uint32_t lowerExpression(const ast::Expression& expr);

    // Helpers
    uint32_t newReg();
    ir::BasicBlock& newBlock(const std::string& label);
    void emit(ir::IRInst inst);
    ir::IRType astTypeToIR(const ast::TypeRef& type);
};

} // namespace mrr
