#include "crypto.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <windows.h>
#include <wincrypt.h>

static void win_crypto_hash(ALG_ID algId, const unsigned char* data, int data_len, char* output_hex) {
    HCRYPTPROV hProv = 0;
    HCRYPTHASH hHash = 0;
    
    if (!CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT)) {
        strcpy(output_hex, "ERROR_ACQUIRE_CONTEXT");
        return;
    }
    
    if (!CryptCreateHash(hProv, algId, 0, 0, &hHash)) {
        CryptReleaseContext(hProv, 0);
        strcpy(output_hex, "ERROR_CREATE_HASH");
        return;
    }
    
    if (!CryptHashData(hHash, data, data_len, 0)) {
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        strcpy(output_hex, "ERROR_HASH_DATA");
        return;
    }
    
    DWORD cbHashSize = 0;
    DWORD dwCount = sizeof(DWORD);
    if (!CryptGetHashParam(hHash, HP_HASHSIZE, (BYTE*)&cbHashSize, &dwCount, 0)) {
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        strcpy(output_hex, "ERROR_HASH_PARAM");
        return;
    }
    
    BYTE* rgbHash = (BYTE*)malloc(cbHashSize);
    if (!CryptGetHashParam(hHash, HP_HASHVAL, rgbHash, &cbHashSize, 0)) {
        free(rgbHash);
        CryptDestroyHash(hHash);
        CryptReleaseContext(hProv, 0);
        strcpy(output_hex, "ERROR_GET_HASHVAL");
        return;
    }
    
    for (DWORD i = 0; i < cbHashSize; i++) {
        sprintf(&output_hex[i * 2], "%02x", rgbHash[i]);
    }
    output_hex[cbHashSize * 2] = '\0';
    
    free(rgbHash);
    CryptDestroyHash(hHash);
    CryptReleaseContext(hProv, 0);
}

void mrr_crypto_md5(const unsigned char* data, int data_len, char* output_hex) {
    win_crypto_hash(CALG_MD5, data, data_len, output_hex);
}

void mrr_crypto_sha256(const unsigned char* data, int data_len, char* output_hex) {
    win_crypto_hash(CALG_SHA_256, data, data_len, output_hex);
}

#else

// For non-Windows platforms, implementing MD5/SHA256 from scratch requires significant code.
// A typical implementation would include OpenSSL or mbedtls.
// Here we provide a stub indicating external linkage is needed for non-Windows.
void mrr_crypto_md5(const unsigned char* data, int data_len, char* output_hex) {
    strcpy(output_hex, "UNSUPPORTED_PLATFORM_STUB_MD5");
}

void mrr_crypto_sha256(const unsigned char* data, int data_len, char* output_hex) {
    strcpy(output_hex, "UNSUPPORTED_PLATFORM_STUB_SHA256");
}

#endif
