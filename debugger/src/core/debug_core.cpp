/*
 * MRR Debugger — Debug Core Stub
 * Phase 1: Skeleton
 */

#include "mrr/core/debug_core.h"

namespace mrr {
namespace debug {

DebugCore::DebugCore() {}
DebugCore::~DebugCore() { detach(); }

// ── Process Control (Phase 3) ──
bool DebugCore::launch(const std::string&, const std::vector<std::string>&) { return false; }
bool DebugCore::attach(uint32_t) { return false; }
bool DebugCore::detach() { return false; }
bool DebugCore::terminate() { return false; }

// ── Execution (Phase 3) ──
bool DebugCore::resume() { return false; }
bool DebugCore::pause() { return false; }
bool DebugCore::stepOver() { return false; }
bool DebugCore::stepInto() { return false; }
bool DebugCore::stepOut() { return false; }

// ── Breakpoints (Phase 3) ──
uint32_t DebugCore::setBreakpoint(const std::string&, uint32_t) { return 0; }
uint32_t DebugCore::setInstructionBreakpoint(uint64_t) { return 0; }
bool DebugCore::removeBreakpoint(uint32_t) { return false; }
std::vector<dap::Breakpoint> DebugCore::getBreakpoints() const { return m_breakpoints; }

// ── Memory (Phase 3) ──
std::vector<uint8_t> DebugCore::readMemory(uint64_t, uint32_t) { return {}; }
bool DebugCore::writeMemory(uint64_t, const std::vector<uint8_t>&) { return false; }

// ── Registers (Phase 3) ──
std::vector<dap::Register> DebugCore::getRegisters() { return {}; }
bool DebugCore::setRegister(const std::string&, uint64_t) { return false; }

// ── Stack & Variables (Phase 3) ──
std::vector<dap::StackFrame> DebugCore::getStackTrace(int) { return {}; }
std::vector<dap::Variable> DebugCore::getVariables(uint32_t) { return {}; }
std::string DebugCore::evaluate(const std::string&) { return ""; }

// ── Disassembly (Phase 3) ──
std::string DebugCore::disassemble(uint64_t, uint32_t) { return ""; }

// ── State ──
TargetState DebugCore::getState() const { return m_state; }
StopReason DebugCore::getStopReason() const { return m_reason; }
uint64_t DebugCore::getPC() const { return m_pc; }

bool DebugCore::waitForDebugEvent() { return false; }
bool DebugCore::handleDebugEvent() { return false; }

} // namespace debug
} // namespace mrr
