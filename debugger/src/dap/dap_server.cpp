/*
 * MRR Debugger — DAP Server Stub
 * Phase 1: Skeleton
 */

#include "mrr/dap/dap_server.h"
#include <iostream>

namespace mrr {
namespace dap {

DAPServer::DAPServer() { registerHandlers(); }

void DAPServer::run() {
    m_running = true;
    sendOutputEvent("console", "[MRR Debugger] Started\n");
    while (m_running) {
        auto msg = readMessage();
        if (msg) dispatch(*msg);
    }
}

void DAPServer::stop() { m_running = false; }

// ── Stubs — Phase 3 ──
void DAPServer::handleInitialize(const Message&) {}
void DAPServer::handleLaunch(const Message&) {}
void DAPServer::handleAttach(const Message&) {}
void DAPServer::handleDisconnect(const Message&) { stop(); }
void DAPServer::handleSetBreakpoints(const Message&) {}
void DAPServer::handleSetInstructionBreakpoints(const Message&) {}
void DAPServer::handleConfigurationDone(const Message&) {}
void DAPServer::handleContinue(const Message&) {}
void DAPServer::handleNext(const Message&) {}
void DAPServer::handleStepIn(const Message&) {}
void DAPServer::handleStepOut(const Message&) {}
void DAPServer::handlePause(const Message&) {}
void DAPServer::handleStackTrace(const Message&) {}
void DAPServer::handleScopes(const Message&) {}
void DAPServer::handleVariables(const Message&) {}
void DAPServer::handleEvaluate(const Message&) {}
void DAPServer::handleReadMemory(const Message&) {}
void DAPServer::handleWriteMemory(const Message&) {}
void DAPServer::handleDisassemble(const Message&) {}
void DAPServer::handleThreads(const Message&) {}

void DAPServer::sendEvent(const std::string&, const std::string&) {}
void DAPServer::sendResponse(const Message&, const std::string&, bool, const std::string&) {}
void DAPServer::sendStoppedEvent(const std::string&, int) {}
void DAPServer::sendOutputEvent(const std::string&, const std::string&) {}

std::optional<Message> DAPServer::readMessage() { return std::nullopt; }
void DAPServer::sendMessage(const std::string&) {}
void DAPServer::dispatch(const Message& msg) {
    auto it = m_handlers.find(msg.command);
    if (it != m_handlers.end()) it->second(msg);
}

void DAPServer::registerHandlers() {
    m_handlers["initialize"]               = [this](auto& m) { handleInitialize(m); };
    m_handlers["launch"]                   = [this](auto& m) { handleLaunch(m); };
    m_handlers["attach"]                   = [this](auto& m) { handleAttach(m); };
    m_handlers["disconnect"]               = [this](auto& m) { handleDisconnect(m); };
    m_handlers["setBreakpoints"]           = [this](auto& m) { handleSetBreakpoints(m); };
    m_handlers["setInstructionBreakpoints"]= [this](auto& m) { handleSetInstructionBreakpoints(m); };
    m_handlers["configurationDone"]        = [this](auto& m) { handleConfigurationDone(m); };
    m_handlers["continue"]                 = [this](auto& m) { handleContinue(m); };
    m_handlers["next"]                     = [this](auto& m) { handleNext(m); };
    m_handlers["stepIn"]                   = [this](auto& m) { handleStepIn(m); };
    m_handlers["stepOut"]                  = [this](auto& m) { handleStepOut(m); };
    m_handlers["pause"]                    = [this](auto& m) { handlePause(m); };
    m_handlers["stackTrace"]               = [this](auto& m) { handleStackTrace(m); };
    m_handlers["scopes"]                   = [this](auto& m) { handleScopes(m); };
    m_handlers["variables"]                = [this](auto& m) { handleVariables(m); };
    m_handlers["evaluate"]                 = [this](auto& m) { handleEvaluate(m); };
    m_handlers["readMemory"]               = [this](auto& m) { handleReadMemory(m); };
    m_handlers["writeMemory"]              = [this](auto& m) { handleWriteMemory(m); };
    m_handlers["disassemble"]              = [this](auto& m) { handleDisassemble(m); };
    m_handlers["threads"]                  = [this](auto& m) { handleThreads(m); };
}

} // namespace dap
} // namespace mrr
