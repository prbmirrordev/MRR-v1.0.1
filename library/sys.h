#ifndef MRR_SYS_H
#define MRR_SYS_H

#ifdef __cplusplus
extern "C" {
#endif

// Exit the program
void mrr_sys_exit(int status);

// Get platform identifier
const char* mrr_sys_platform();

// Get MRR/Library version
const char* mrr_sys_version();

// Simulate sys.getsizeof for a basic datatype
size_t mrr_sys_getsizeof(int type_id);

#ifdef __cplusplus
}
#endif

#endif // MRR_SYS_H
