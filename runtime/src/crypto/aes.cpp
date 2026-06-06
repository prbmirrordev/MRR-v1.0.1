/*
 * MRR Runtime — AES Cryptographic Primitives Stub
 * Phase 1: Placeholder
 */

extern "C" {

int mrr_aes256_encrypt(const void* key, const void* input, 
                        void* output, unsigned int size) {
    (void)key; (void)input; (void)output; (void)size;
    return -1; // Not implemented
}

int mrr_aes256_decrypt(const void* key, const void* input,
                        void* output, unsigned int size) {
    (void)key; (void)input; (void)output; (void)size;
    return -1; // Not implemented
}

} // extern "C"
