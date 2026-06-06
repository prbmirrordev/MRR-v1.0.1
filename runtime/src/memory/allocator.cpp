/*
 * MRR Runtime — Memory Allocator Stub
 * Custom allocator with security features:
 *   - Zero-on-free (prevents data leakage)
 *   - Guard pages
 *   - Pool-based allocation for exploit payloads
 */

#include <cstdlib>
#include <cstring>
#include <cstdint>

extern "C" {

void* mrr_alloc(size_t size) {
    return std::malloc(size);
}

void* mrr_alloc_zeroed(size_t size) {
    void* ptr = std::malloc(size);
    if (ptr) std::memset(ptr, 0, size);
    return ptr;
}

void mrr_free(void* ptr, size_t size) {
    if (ptr) {
        // Security: zero memory before freeing
        std::memset(ptr, 0, size);
        std::free(ptr);
    }
}

void mrr_memcpy(void* dst, const void* src, size_t size) {
    std::memcpy(dst, src, size);
}

void mrr_memset(void* dst, uint8_t val, size_t size) {
    std::memset(dst, val, size);
}

// Volatile memset — cannot be optimized away by compiler
void mrr_secure_zero(void* ptr, size_t size) {
    volatile uint8_t* p = static_cast<volatile uint8_t*>(ptr);
    for (size_t i = 0; i < size; i++) {
        p[i] = 0;
    }
}

} // extern "C"
