#ifndef MRR_XOR_H
#define MRR_XOR_H

#ifdef __cplusplus
extern "C" {
#endif

// Encrypt/Decrypt data using XOR cipher
// The output buffer must be pre-allocated and at least 'data_len' bytes long
void mrr_xor_cipher(const unsigned char* data, int data_len, const char* key, int key_len, unsigned char* output);

// Brute-force/Crack XOR key given a known plaintext string
// Returns the discovered key (must be freed) or NULL if not found
char* mrr_xor_crack_known_plaintext(const unsigned char* ciphertext, int cipher_len, const char* known_plaintext);

#ifdef __cplusplus
}
#endif

#endif // MRR_XOR_H
