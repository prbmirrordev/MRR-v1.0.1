#include "xor.h"
#include <stdlib.h>
#include <string.h>

void mrr_xor_cipher(const unsigned char* data, int data_len, const char* key, int key_len, unsigned char* output) {
    if (!data || !key || key_len <= 0 || !output) return;
    
    for (int i = 0; i < data_len; i++) {
        output[i] = data[i] ^ key[i % key_len];
    }
}

char* mrr_xor_crack_known_plaintext(const unsigned char* ciphertext, int cipher_len, const char* known_plaintext) {
    if (!ciphertext || !known_plaintext) return NULL;
    
    int kp_len = strlen(known_plaintext);
    if (kp_len > cipher_len) return NULL; // Plaintext longer than cipher
    
    // Attempt to recover key by XORing cipher with known plaintext.
    // If the key length is equal to or less than the known plaintext length,
    // this will reveal the key.
    char* potential_key = (char*)malloc(kp_len + 1);
    
    for (int i = 0; i < kp_len; i++) {
        potential_key[i] = ciphertext[i] ^ known_plaintext[i];
    }
    potential_key[kp_len] = '\0';
    
    // In a real scenario, you'd try to find the repeating pattern in potential_key
    // to find the exact key length. This is a simplified crack.
    return potential_key;
}
