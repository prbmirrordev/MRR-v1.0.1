#ifndef MRR_CRYPTO_H
#define MRR_CRYPTO_H

#ifdef __cplusplus
extern "C" {
#endif

// Calculate MD5 Hash of data
// Output buffer must be at least 33 bytes to hold the 32-character hex string + null terminator
void mrr_crypto_md5(const unsigned char* data, int data_len, char* output_hex);

// Calculate SHA-256 Hash of data
// Output buffer must be at least 65 bytes to hold the 64-character hex string + null terminator
void mrr_crypto_sha256(const unsigned char* data, int data_len, char* output_hex);

#ifdef __cplusplus
}
#endif

#endif // MRR_CRYPTO_H
