/*
 * MRR Runtime — Syscall Wrappers Stub
 * Phase 1: Placeholder for direct syscall invocation
 */

#include <cstdint>

extern "C" {

// Direct syscall stub — will be implemented with inline asm in Phase 3
// Bypasses ntdll.dll for stealth
int64_t mrr_syscall(uint32_t syscall_number, ...) {
    (void)syscall_number;
    return -1; // Not implemented
}

} // extern "C"
