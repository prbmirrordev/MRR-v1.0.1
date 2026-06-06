/*
 * MRR Debugger — Main Entry Point
 */

#include "mrr/dap/dap_server.h"
#include <iostream>

int main(int argc, char* argv[]) {
    std::cerr << "[MRR-DBG] MRR Debugger v0.1.0\n";
    std::cerr << "[MRR-DBG] Debug Adapter Protocol Server\n";

    mrr::dap::DAPServer server;
    server.run();

    return 0;
}
