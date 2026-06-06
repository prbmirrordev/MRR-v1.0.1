/*
 * MRR Compiler — Main Entry Point
 */

#include "mrr/driver/cli.h"
#include <iostream>

int main(int argc, char* argv[]) {
    auto options = mrr::parseArgs(argc, argv);
    if (!options.has_value()) {
        return 1;
    }

    return mrr::compileFile(options.value());
}
