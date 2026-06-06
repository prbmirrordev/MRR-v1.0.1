/*
 * MRR Debugger — Debug Core Interface
 * Phase 1: Skeleton
 *
 * Core debug engine for process control, breakpoints,
 * memory inspection, and register access.
 */

#pragma once

#include "mrr/dap/dap_server.h"
#include <string>
#include <vector>
#include <cstdint>

namespace mrr {
namespace debug {

// ─── Debug Target State ───
enum class TargetState {
    NotStarted,
    Running,
    Stopped,
    Exited,
    Crashed
};

// ─── Stop Reason ───
enum class StopReason {
    Breakpoint,
    Step,
    Pause,
    Exception,
    Entry
};

// ─── Debug Core ───
class DebugCore {
public:
    DebugCore();
    ~DebugCore();

    // ── Process Control ──
    bool launch(const std::string& executable, 
                const std::vector<std::string>& args = {});
    bool attach(uint32_t pid);
    bool detach();
    bool terminate();

    // ── Execution Control ──
    bool resume();
    bool pause();
    bool stepOver();
    bool stepInto();
    bool stepOut();

    // ── Breakpoints ──
    uint32_t setBreakpoint(const std::string& file, uint32_t line);
    uint32_t setInstructionBreakpoint(uint64_t address);
    bool     removeBreakpoint(uint32_t id);
    std::vector<dap::Breakpoint> getBreakpoints() const;

    // ── Memory Access (Critical for MRR) ──
    std::vector<uint8_t> readMemory(uint64_t address, uint32_t size);
    bool writeMemory(uint64_t address, const std::vector<uint8_t>& data);

    // ── Registers ──
    std::vector<dap::Register> getRegisters();
    bool setRegister(const std::string& name, uint64_t value);

    // ── Stack & Variables ──
    std::vector<dap::StackFrame> getStackTrace(int maxFrames = 20);
    std::vector<dap::Variable> getVariables(uint32_t scopeId);
    std::string evaluate(const std::string& expression);

    // ── Disassembly ──
    std::string disassemble(uint64_t address, uint32_t count);

    // ── State ──
    [[nodiscard]] TargetState getState() const;
    [[nodiscard]] StopReason  getStopReason() const;
    [[nodiscard]] uint64_t    getPC() const;  // Program Counter

private:
    TargetState m_state  = TargetState::NotStarted;
    StopReason  m_reason = StopReason::Entry;
    uint64_t    m_pc     = 0;

    // Platform-specific debug handles
    void*    m_processHandle = nullptr;
    uint32_t m_processId     = 0;
    uint32_t m_threadId      = 0;

    std::vector<dap::Breakpoint> m_breakpoints;
    uint32_t m_nextBreakpointId = 1;

    // Internal helpers
    bool waitForDebugEvent();
    bool handleDebugEvent();
};

} // namespace debug
} // namespace mrr
