#include "random.h"
#include <stdlib.h>
#include <time.h>

#ifdef _WIN32
#include <windows.h>
#include <wincrypt.h>
#else
#include <stdio.h>
#endif

static int random_seeded = 0;

void mrr_random_seed(unsigned int seed) {
    srand(seed);
    random_seeded = 1;
}

double mrr_random_random() {
    if (!random_seeded) {
        srand((unsigned int)time(NULL));
        random_seeded = 1;
    }
    return (double)rand() / (double)RAND_MAX;
}

int mrr_random_randint(int min, int max) {
    if (!random_seeded) {
        srand((unsigned int)time(NULL));
        random_seeded = 1;
    }
    if (max < min) return min;
    return min + (rand() % (max - min + 1));
}

int mrr_random_secure_bytes(unsigned char* buffer, int length) {
#ifdef _WIN32
    HCRYPTPROV hProvider;
    if (!CryptAcquireContext(&hProvider, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
        return 0; // Failed
    }
    if (!CryptGenRandom(hProvider, length, buffer)) {
        CryptReleaseContext(hProvider, 0);
        return 0; // Failed
    }
    CryptReleaseContext(hProvider, 0);
    return 1; // Success
#else
    FILE* fp = fopen("/dev/urandom", "rb");
    if (!fp) return 0;
    size_t read_bytes = fread(buffer, 1, length, fp);
    fclose(fp);
    return read_bytes == length ? 1 : 0;
#endif
}
