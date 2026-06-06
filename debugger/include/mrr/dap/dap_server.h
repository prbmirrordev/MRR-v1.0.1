/*
 * MRR Debugger — Debug Adapter Protocol (DAP) Server Skeleton
 * Phase 1: Interface definitions and message types
 *
 * The MRR debugger communicates with VS/VSCode via the
 * Debug Adapter Protocol (JSON-RPC over stdin/stdout).
 */

#pragma once

#include <string>
#include <vector>
#include <unordered_map>
#include <functional>
#include <cstdint>
#include <optional>

namespace mrr {
namespace dap {

// ─── DAP Message Types ───

enum class MessageType {
    Request,
    Response,
    Event
};

struct Message {
    int          seq  = 0;
    MessageType  type = MessageType::Request;
    std::string  command;
    std::string  body_json;  // Raw JSON body
};

// ─── DAP Capabilities ───

struct Capabilities {
    bool supportsConfigurationDoneRequest = true;
    bool supportsFunctionBreakpoints      = true;
    bool supportsConditionalBreakpoints   = true;
    bool supportsEvaluateForHovers        = true;
    bool supportsSetVariable              = true;
    bool supportsStepBack                 = false;
    bool supportsReadMemoryRequest        = true;   // Critical for MRR
    bool supportsWriteMemoryRequest       = true;   // Critical for MRR
    bool supportsDisassembleRequest       = true;   // Critical for MRR
    bool supportsInstructionBreakpoints   = true;
};

// ─── Breakpoint ───

struct Breakpoint {
    uint32_t     id       = 0;
    bool         verified = false;
    std::string  source_path;
    uint32_t     line     = 0;
    std::string  condition;
    uint64_t     address  = 0;  // For instruction breakpoints
};

// ─── Stack Frame ───

struct StackFrame {
    uint32_t    id = 0;
    std::string name;
    std::string source_path;
    uint32_t    line   = 0;
    uint32_t    column = 0;
    uint64_t    instruction_pointer = 0;
};

// ─── Variable ───

struct Variable {
    std::string  name;
    std::string  value;
    std::string  type;
    uint32_t     variables_reference = 0;  // For expandable vars
    uint64_t     memory_reference    = 0;  // Direct memory address
};

// ─── Register ───

struct Register {
    std::string name;
    uint64_t    value;
    std::string display;   // Formatted hex string
};

// ─── Memory Region ───

struct MemoryRegion {
    uint64_t    address;
    uint32_t    size;
    std::vector<uint8_t> data;
};

// ─── DAP Server (Interface) ───

class DAPServer {
public:
    DAPServer();
    virtual ~DAPServer() = default;

    /// Start the DAP server (reads from stdin, writes to stdout)
    void run();

    /// Stop the server
    void stop();

protected:
    // ── DAP Request Handlers (to be implemented) ──
    virtual void handleInitialize(const Message& request);
    virtual void handleLaunch(const Message& request);
    virtual void handleAttach(const Message& request);
    virtual void handleDisconnect(const Message& request);
    virtual void handleSetBreakpoints(const Message& request);
    virtual void handleSetInstructionBreakpoints(const Message& request);
    virtual void handleConfigurationDone(const Message& request);
    virtual void handleContinue(const Message& request);
    virtual void handleNext(const Message& request);       // Step over
    virtual void handleStepIn(const Message& request);
    virtual void handleStepOut(const Message& request);
    virtual void handlePause(const Message& request);
    virtual void handleStackTrace(const Message& request);
    virtual void handleScopes(const Message& request);
    virtual void handleVariables(const Message& request);
    virtual void handleEvaluate(const Message& request);
    virtual void handleReadMemory(const Message& request);
    virtual void handleWriteMemory(const Message& request);
    virtual void handleDisassemble(const Message& request);
    virtual void handleThreads(const Message& request);

    // ── Event Emitters ──
    void sendEvent(const std::string& event, const std::string& body = "{}");
    void sendResponse(const Message& request, const std::string& body = "{}",
                      bool success = true, const std::string& message = "");
    void sendStoppedEvent(const std::string& reason, int threadId = 1);
    void sendOutputEvent(const std::string& category,
                         const std::string& output);

private:
    bool        m_running = false;
    int         m_seq     = 1;
    Capabilities m_capabilities;

    // Message I/O
    std::optional<Message> readMessage();
    void sendMessage(const std::string& json);
    void dispatch(const Message& message);

    using Handler = std::function<void(const Message&)>;
    std::unordered_map<std::string, Handler> m_handlers;
    void registerHandlers();
};

} // namespace dap
} // namespace mrr
