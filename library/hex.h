#ifndef MRR_HEX_H
#define MRR_HEX_H

#ifdef __cplusplus
extern "C" {
#endif

// Convert raw bytes to a hexadecimal string.
// Caller must free the returned string.
char* mrr_hex_encode(const unsigned char* data, int data_len);

// Convert a hexadecimal string to raw bytes.
// 'out_len' will contain the length of the resulting byte array.
// Caller must free the returned byte array.
unsigned char* mrr_hex_decode(const char* hex_str, int* out_len);

#ifdef __cplusplus
}
#endif

#endif // MRR_HEX_H
