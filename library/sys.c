#include "sys.h"
#include <stdlib.h>
#include <stdio.h>

void mrr_sys_exit(int status) {
    exit(status);
}

const char* mrr_sys_platform() {
#ifdef _WIN32
    return "win32";
#elif __APPLE__
    return "darwin";
#elif __linux__
    return "linux";
#else
    return "unknown";
#endif
}

const char* mrr_sys_version() {
    return "MRR C-Library 1.0.0 (GCC/MSVC Compat)";
}

size_t mrr_sys_getsizeof(int type_id) {
    // 1: int, 2: char, 3: float, 4: double, 5: pointer
    switch(type_id) {
        case 1: return sizeof(int);
        case 2: return sizeof(char);
        case 3: return sizeof(float);
        case 4: return sizeof(double);
        case 5: return sizeof(void*);
        default: return 0;
    }
}
