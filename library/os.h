#ifndef MRR_OS_H
#define MRR_OS_H

#ifdef __cplusplus
extern "C" {
#endif

// File operations
int mrr_os_mkdir(const char* path);
int mrr_os_rmdir(const char* path);
int mrr_os_remove(const char* path);
int mrr_os_rename(const char* old_name, const char* new_name);

// System environment
char* mrr_os_getcwd();
char* mrr_os_getenv(const char* name);
int mrr_os_setenv(const char* name, const char* value, int overwrite);

// Process execution
int mrr_os_system(const char* command);

// Platform info
const char* mrr_os_name();

#ifdef __cplusplus
}
#endif

#endif // MRR_OS_H
