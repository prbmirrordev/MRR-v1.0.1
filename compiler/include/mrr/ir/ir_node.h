/*
 * MRR Compiler — Intermediate Representation
 */

#pragma once

#include <string>
#include <vector>
#include <memory>
#include <cstdint>

namespace mrr {
namespace ir {

// ─── IR Opcodes ───
enum class IROpcode : uint16_t {
    // Constants
    Const_I32,
    Const_I64,
    Const_F64,
    Const_Str,
    Const_Null,
    Const_Bool,
    Const_Bytes,      // Raw byte array (for shellcode)

    // Arithmetic
    Add, Sub, Mul, Div, Mod, Neg,

    // Bitwise
    And, Or, Xor, Not, Shl, Shr,

    // Comparison
    Eq, Ne, Lt, Gt, Le, Ge,

    // Memory
    Load, Store,
    Alloca,           // Stack allocation
    HeapAlloc,        // Heap allocation
    HeapFree,
    MemCopy,
    MemSet,
    VolatileLoad,     // Volatile read
    VolatileStore,    // Volatile write

    // Pointer
    PtrAdd,
    PtrSub,
    PtrToInt,
    IntToPtr,
    AddrOf,
    Deref,

    // Control Flow
    Jump,
    Branch,           // Conditional jump
    Call,
    Return,
    Phi,

    // Ring-0 / Cyber
    Syscall,          // System call invocation
    PortIn,           // I/O port read
    PortOut,          // I/O port write
    Interrupt,        // Software interrupt (INT instruction)
    InlineAsm,        // Inline assembly blob
    ShellcodeEmit,    // Emit raw shellcode bytes

    // Misc
    Cast,
    Nop
};

// ─── IR Value Types ───
enum class IRType : uint8_t {
    Void, I8, I16, I32, I64, I128,
    U8, U16, U32, U64, U128,
    F32, F64, Bool, Ptr, Bytes,
    Struct, Array
};

// ─── IR Instruction ───
struct IRInst {
    IROpcode             opcode;
    IRType               result_type = IRType::Void;
    uint32_t             result_reg  = 0;
    std::vector<uint32_t> operands;        // Register indices
    std::string          str_data;          // For strings, asm, labels
    std::vector<uint8_t> byte_data;         // For raw bytes/shellcode

    uint32_t             source_line = 0;   // Debug info: source line
};

// ─── Basic Block ───
struct BasicBlock {
    std::string            label;
    std::vector<IRInst>    instructions;
    std::vector<uint32_t>  predecessors;
    std::vector<uint32_t>  successors;
};

// ─── IR Function ───
struct IRFunction {
    std::string                        name;
    IRType                             return_type = IRType::Void;
    std::vector<std::pair<IRType, std::string>> params;
    std::vector<BasicBlock>            blocks;
    uint32_t                           next_reg = 0;
    bool                               is_kernel = false;
    bool                               is_unsafe = false;
    std::string                        calling_conv;
};

// ─── IR Module (top-level) ───
struct IRModule {
    std::string                             name;
    std::vector<std::unique_ptr<IRFunction>> functions;
    std::vector<std::pair<std::string, std::vector<uint8_t>>> globals;
    std::vector<std::string>                string_table;
};

} // namespace ir
} // namespace mrr
