/*
 * MRR Compiler — x86_64 Code Generator Interface
 */

#pragma once

#include "mrr/ir/ir_node.h"
#include <string>
#include <vector>
#include <memory>
#include <cstdint>

namespace mrr {

// ─── Output Format ───
enum class OutputFormat {
    Assembly,         // .asm NASM syntax
    ObjectFile,       // .o / .obj (via nasm/ml64)
    Executable,       // Linked executable
    Shellcode,        // Raw bytes, position-independent
    KernelDriver      // Windows .sys or Linux .ko skeleton
};

// ─── Code Generation Options ───
struct CodegenOptions {
    OutputFormat   format     = OutputFormat::Assembly;
    bool           emit_debug = false;
    bool           optimize   = false;
    std::string    entry_point = "main";
    std::string    target_os  = "windows";   // "windows" | "linux"
};

class X86_64Emitter {
public:
    explicit X86_64Emitter(const CodegenOptions& options);

    /// Generate assembly from IR module
    std::string emit(const ir::IRModule& module);

    /// Generate raw shellcode bytes
    std::vector<uint8_t> emitShellcode(const ir::IRModule& module);

private:
    CodegenOptions m_options;
    std::string    m_output;
    uint32_t       m_labelCounter = 0;

    // Emission helpers
    void emitFunction(const ir::IRFunction& func);
    void emitBlock(const ir::BasicBlock& block);
    void emitInstruction(const ir::IRInst& inst);

    // Register allocation (simple linear scan placeholder)
    std::string regName(uint32_t reg, ir::IRType type);
    void emitPrologue(const ir::IRFunction& func);
    void emitEpilogue(const ir::IRFunction& func);

    // Specific instruction emission
    void emitArithmetic(const ir::IRInst& inst);
    void emitMemory(const ir::IRInst& inst);
    void emitControl(const ir::IRInst& inst);
    void emitSyscall(const ir::IRInst& inst);
    void emitPortIO(const ir::IRInst& inst);
    void emitInlineAsm(const ir::IRInst& inst);

    // Helpers
    std::string newLabel();
    void line(const std::string& text);
    void comment(const std::string& text);
};

class Codegen {
public:
    explicit Codegen(const CodegenOptions& options);

    /// Full code generation pipeline: IR → Assembly → Object
    bool generate(const ir::IRModule& module, const std::string& outputPath);

private:
    CodegenOptions m_options;
    X86_64Emitter  m_emitter;

    bool assembleNASM(const std::string& asmPath, const std::string& objPath);
    bool linkExecutable(const std::string& objPath, const std::string& exePath);
};

} // namespace mrr
