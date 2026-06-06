#include "hex.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>

char* mrr_hex_encode(const unsigned char* data, int data_len) {
    if (!data || data_len <= 0) return NULL;
    
    char* hex_str = (char*)malloc(data_len * 2 + 1);
    if (!hex_str) return NULL;
    
    for (int i = 0; i < data_len; i++) {
        sprintf(&hex_str[i * 2], "%02x", data[i]);
    }
    hex_str[data_len * 2] = '\0';
    return hex_str;
}

static int hex_char_to_int(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return -1;
}

unsigned char* mrr_hex_decode(const char* hex_str, int* out_len) {
    if (!hex_str || !out_len) return NULL;
    
    int len = strlen(hex_str);
    if (len % 2 != 0) return NULL; // Invalid hex string length
    
    int byte_len = len / 2;
    unsigned char* raw_bytes = (unsigned char*)malloc(byte_len);
    if (!raw_bytes) return NULL;
    
    for (int i = 0; i < byte_len; i++) {
        int high = hex_char_to_int(hex_str[i * 2]);
        int low = hex_char_to_int(hex_str[i * 2 + 1]);
        
        if (high == -1 || low == -1) {
            free(raw_bytes);
            return NULL;
        }
        
        raw_bytes[i] = (unsigned char)((high << 4) | low);
    }
    
    *out_len = byte_len;
    return raw_bytes;
}
