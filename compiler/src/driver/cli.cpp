/*
 * MRR Compiler — CLI Driver
 * Phase 1: Skeleton with argument parsing and pipeline skeleton
 */

#include "mrr/driver/cli.h"
#include <iostream>
#include <string>

namespace mrr {

std::optional<CompilerOptions> parseArgs(int argc, char* argv[]) {
    CompilerOptions opts;

    if (argc < 2) {
        return std::nullopt;
    }

    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];

        if (arg == "-h" || arg == "--help") {
            printUsage();
            return std::nullopt;
        }
        else if (arg == "-v" || arg == "--version") {
            printVersion();
            return std::nullopt;
        }
        else if (arg == "-o" || arg == "--output") {
            if (i + 1 < argc) opts.output_file = argv[++i];
        }
        else if (arg == "--emit-ast") {
            opts.emit_ast = true;
        }
        else if (arg == "--emit-ir") {
            opts.emit_ir = true;
        }
        else if (arg == "--emit-asm") {
            opts.emit_asm = true;
        }
        else if (arg == "-g" || arg == "--debug") {
            opts.debug_info = true;
        }
        else if (arg == "-O" || arg == "--optimize") {
            opts.optimize = true;
        }
        else if (arg == "--verbose") {
            opts.verbose = true;
        }
        else if (arg == "--shellcode") {
            opts.output_format = OutputFormat::Shellcode;
        }
        else if (arg == "--driver") {
            opts.output_format = OutputFormat::KernelDriver;
        }
        else if (arg == "--target") {
            if (i + 1 < argc) opts.target_os = argv[++i];
        }
        else if (arg[0] == '-') {
            std::cerr << "mrrc: unknown option '" << arg << "'\n";
            return std::nullopt;
        }
        else {
            opts.input_file = arg;
        }
    }

    if (opts.input_file.empty()) {
        std::cerr << "mrrc: no input file specified\n";
        return std::nullopt;
    }

    if (opts.output_file.empty()) {
        // Derive output from input
        auto dot = opts.input_file.rfind('.');
        std::string base = (dot != std::string::npos)
            ? opts.input_file.substr(0, dot)
            : opts.input_file;

        switch (opts.output_format) {
            case OutputFormat::Assembly:    opts.output_file = base + ".asm"; break;
            case OutputFormat::ObjectFile:  opts.output_file = base + ".obj"; break;
            case OutputFormat::Executable:  opts.output_file = base + ".exe"; break;
            case OutputFormat::Shellcode:   opts.output_file = base + ".bin"; break;
            case OutputFormat::KernelDriver:opts.output_file = base + ".sys"; break;
        }
    }

    return opts;
}

void printUsage() {
    std::cout << R"(
╔══════════════════════════════════════════════════════════════╗
║                    MRR Compiler v0.1.0                       ║
║         Memory · Registers · Rings                           ║
╚══════════════════════════════════════════════════════════════╝

USAGE:
    mrrc [OPTIONS] <input.mrr>

OPTIONS:
    -o, --output <file>     Set output file path
    -g, --debug             Emit debug information
    -O, --optimize          Enable optimizations
    --emit-ast              Print AST to stdout
    --emit-ir               Print IR to stdout
    --emit-asm              Output assembly instead of binary
    --shellcode             Generate position-independent shellcode
    --driver                Generate kernel driver skeleton
    --target <os>           Target OS (windows | linux)
    --verbose               Verbose compiler output
    -v, --version           Print version
    -h, --help              Show this help

EXAMPLES:
    mrrc hello.mrr                    Compile to executable
    mrrc --shellcode payload.mrr      Compile to raw shellcode
    mrrc --driver mydriver.mrr        Compile as kernel driver
    mrrc --emit-ast -o ast.json x.mrr Dump AST

)" << std::endl;
}

void printVersion() {
    std::cout << "mrrc (MRR Compiler) version 0.1.0\n"
              << "Target: x86_64\n"
              << "Build: Phase 1 — Skeleton\n";
}

int compileFile(const CompilerOptions& options) {
    if (options.verbose) {
        std::cout << "[mrrc] Input:  " << options.input_file << "\n"
                  << "[mrrc] Output: " << options.output_file << "\n"
                  << "[mrrc] Target: " << options.target_os << "\n";
    }

    // TODO: Phase 2/3 — Full compilation pipeline
    // 1. Read source file
    // 2. Lex → Token stream
    // 3. Parse → AST
    // 4. Sema → Type-checked AST
    // 5. Lower → IR
    // 6. Codegen → Assembly / Object / Executable

    std::cerr << "[mrrc] Compilation pipeline not yet implemented (Phase 1 Skeleton)\n";
    return 1;
}

} // namespace mrr
