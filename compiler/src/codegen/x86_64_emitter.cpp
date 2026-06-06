/*
 * MRR Compiler — x86_64 Emitter (Stub)
 * Phase 1: Skeleton — full assembly emission in Phase 3
 */

#include "mrr/codegen/codegen.h"
#include <sstream>

namespace mrr {

X86_64Emitter::X86_64Emitter(const CodegenOptions& options)
    : m_options(options) {}

std::string X86_64Emitter::emit(const ir::IRModule& module) {
    m_output.clear();

    // NASM-style header
    line("; ═══════════════════════════════════════════════");
    line("; MRR Compiler — Generated x86_64 Assembly");
    line("; Module: " + module.name);
    line("; Target: " + m_options.target_os);
    line("; ═══════════════════════════════════════════════");
    line("");

    if (m_options.target_os == "windows") {
        line("bits 64");
        line("default rel");
        line("");
        line("section .text");
    } else {
        line("bits 64");
        line("");
        line("section .text");
        line("global _start");
    }

    line("");

    for (const auto& func : module.functions) {
        if (func) emitFunction(*func);
    }

    return m_output;
}

std::vector<uint8_t> X86_64Emitter::emitShellcode(const ir::IRModule&) {
    // TODO: Phase 3 — position-independent shellcode generation
    return {};
}

// ── Stubs (Phase 3) ──
void X86_64Emitter::emitFunction(const ir::IRFunction&) {}
void X86_64Emitter::emitBlock(const ir::BasicBlock&) {}
void X86_64Emitter::emitInstruction(const ir::IRInst&) {}
std::string X86_64Emitter::regName(uint32_t, ir::IRType) { return "rax"; }
void X86_64Emitter::emitPrologue(const ir::IRFunction&) {}
void X86_64Emitter::emitEpilogue(const ir::IRFunction&) {}
void X86_64Emitter::emitArithmetic(const ir::IRInst&) {}
void X86_64Emitter::emitMemory(const ir::IRInst&) {}
void X86_64Emitter::emitControl(const ir::IRInst&) {}
void X86_64Emitter::emitSyscall(const ir::IRInst&) {}
void X86_64Emitter::emitPortIO(const ir::IRInst&) {}
void X86_64Emitter::emitInlineAsm(const ir::IRInst&) {}

std::string X86_64Emitter::newLabel() {
    return ".L" + std::to_string(m_labelCounter++);
}

void X86_64Emitter::line(const std::string& text) {
    m_output += text + "\n";
}

void X86_64Emitter::comment(const std::string& text) {
    m_output += "; " + text + "\n";
}

// ─── Codegen Pipeline ───

Codegen::Codegen(const CodegenOptions& options)
    : m_options(options)
    , m_emitter(options) {}

bool Codegen::generate(const ir::IRModule& module, const std::string& outputPath) {
    // Phase 3: Full pipeline IR → ASM → OBJ → EXE
    auto asmCode = m_emitter.emit(module);
    // TODO: Write to file and invoke assembler
    (void)outputPath;
    return !asmCode.empty();
}

bool Codegen::assembleNASM(const std::string&, const std::string&) {
    // TODO: Phase 3
    return false;
}

bool Codegen::linkExecutable(const std::string&, const std::string&) {
    // TODO: Phase 3
    return false;
}

} // namespace mrr
