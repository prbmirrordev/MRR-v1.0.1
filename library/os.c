#include "os.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <direct.h>
#include <windows.h>
#else
#include <sys/stat.h>
#include <unistd.h>
#endif

int mrr_os_mkdir(const char* path) {
#ifdef _WIN32
    return _mkdir(path);
#else
    return mkdir(path, 0777);
#endif
}

int mrr_os_rmdir(const char* path) {
#ifdef _WIN32
    return _rmdir(path);
#else
    return rmdir(path);
#endif
}

int mrr_os_remove(const char* path) {
    return remove(path);
}

int mrr_os_rename(const char* old_name, const char* new_name) {
    return rename(old_name, new_name);
}

char* mrr_os_getcwd() {
    char* buffer = (char*)malloc(1024);
#ifdef _WIN32
    if (_getcwd(buffer, 1024) != NULL) return buffer;
#else
    if (getcwd(buffer, 1024) != NULL) return buffer;
#endif
    free(buffer);
    return NULL;
}

char* mrr_os_getenv(const char* name) {
    char* val = getenv(name);
    if (val) return strdup(val);
    return NULL;
}

int mrr_os_setenv(const char* name, const char* value, int overwrite) {
#ifdef _WIN32
    return _putenv_s(name, value);
#else
    return setenv(name, value, overwrite);
#endif
}

int mrr_os_system(const char* command) {
    return system(command);
}

const char* mrr_os_name() {
#ifdef _WIN32
    return "nt";
#elif __APPLE__
    return "darwin";
#elif __linux__
    return "posix";
#else
    return "unknown";
#endif
}
