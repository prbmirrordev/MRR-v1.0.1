/*
 * MRR Compiler — CLI Driver Interface
 */

#pragma once

#include <string>
#include <vector>
#include <optional>
#include "mrr/codegen/codegen.h"

namespace mrr {

struct CompilerOptions {
    std::string              input_file;
    std::string              output_file;
    OutputFormat             output_format = OutputFormat::Executable;
    bool                     emit_ast      = false;
    bool                     emit_ir       = false;
    bool                     emit_asm      = false;
    bool                     debug_info    = false;
    bool                     optimize      = false;
    bool                     verbose       = false;
    std::string              target_os     = "windows";
    std::vector<std::string> include_paths;
    std::vector<std::string> link_libs;
};

/// Parse CLI arguments into CompilerOptions
std::optional<CompilerOptions> parseArgs(int argc, char* argv[]);

/// Print usage / help text
void printUsage();

/// Print compiler version
void printVersion();

/// Run the full compilation pipeline
int compileFile(const CompilerOptions& options);

} // namespace mrr
