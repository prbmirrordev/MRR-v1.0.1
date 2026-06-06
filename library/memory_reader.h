/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Memory Reader — Out-of-Process Memory Access Library       ║
 * ║                                                                  ║
 * ║  Windows API (ReadProcessMemory) ve Linux (ptrace / /proc)      ║
 * ║  kullanarak harici süreçlerin belleğini okur.                   ║
 * ║                                                                  ║
 * ║  GÜVENLİK: Bu kütüphane SADECE MRR'ın "unsafe" veya "exploit"  ║
 * ║  blokları içinden çağrılabilir.                                 ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#ifndef MRR_MEMORY_READER_H
#define MRR_MEMORY_READER_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* ═══════════════════════════════════════════════════════════
 * Hata Kodları
 * ═══════════════════════════════════════════════════════════ */
#define MRR_MEM_OK                  0
#define MRR_MEM_ERR_NOT_FOUND      -1
#define MRR_MEM_ERR_ACCESS_DENIED  -2
#define MRR_MEM_ERR_INVALID_HANDLE -3
#define MRR_MEM_ERR_READ_FAILED    -4
#define MRR_MEM_ERR_INVALID_PARAM  -5
#define MRR_MEM_ERR_MODULE_NOT_FOUND -6

/* ═══════════════════════════════════════════════════════════
 * Veri Yapıları
 * ═══════════════════════════════════════════════════════════ */

/* Process bilgisi */
typedef struct {
    uint32_t pid;
    char     name[260];
} MRR_ProcessInfo;

/* Modül bilgisi */
typedef struct {
    uintptr_t base_address;
    uint32_t  size;
    char      name[260];
    char      path[520];
} MRR_ModuleInfo;

/* Memory Reader handle */
typedef struct {
    void*     native_handle;   /* HANDLE (Windows) veya pid_t (Linux) */
    uint32_t  pid;
    int       is_attached;
    char      process_name[260];
} MRR_MemoryReader;

/* ═══════════════════════════════════════════════════════════
 * Process Keşfi
 * ═══════════════════════════════════════════════════════════ */

/* Çalışan tüm process'leri listele */
int mrr_mem_get_process_list(MRR_ProcessInfo* out_list, int max_count, int* out_count);

/* İsme göre PID bul */
int mrr_mem_find_process_by_name(const char* name, uint32_t* out_pid);

/* ═══════════════════════════════════════════════════════════
 * Process Bağlantısı
 * ═══════════════════════════════════════════════════════════ */

/* PID ile process'e bağlan */
int mrr_mem_attach_pid(MRR_MemoryReader* reader, uint32_t pid);

/* İsim ile process'e bağlan */
int mrr_mem_attach_name(MRR_MemoryReader* reader, const char* process_name);

/* Process bağlantısını kes */
int mrr_mem_detach(MRR_MemoryReader* reader);

/* ═══════════════════════════════════════════════════════════
 * Modül Bilgisi
 * ═══════════════════════════════════════════════════════════ */

/* Modül taban adresini al */
int mrr_mem_get_module_base(MRR_MemoryReader* reader, const char* module_name,
                            uintptr_t* out_base);

/* Modül listesini al */
int mrr_mem_get_module_list(MRR_MemoryReader* reader, MRR_ModuleInfo* out_list,
                            int max_count, int* out_count);

/* ═══════════════════════════════════════════════════════════
 * Bellek Okuma — Tipli
 * ═══════════════════════════════════════════════════════════ */

/* Ham bytes oku */
int mrr_mem_read_bytes(MRR_MemoryReader* reader, uintptr_t address,
                       void* buffer, size_t size, size_t* bytes_read);

/* Tipli okumalar */
int mrr_mem_read_i32(MRR_MemoryReader* reader, uintptr_t address, int32_t* out_value);
int mrr_mem_read_i64(MRR_MemoryReader* reader, uintptr_t address, int64_t* out_value);
int mrr_mem_read_u32(MRR_MemoryReader* reader, uintptr_t address, uint32_t* out_value);
int mrr_mem_read_u64(MRR_MemoryReader* reader, uintptr_t address, uint64_t* out_value);
int mrr_mem_read_f32(MRR_MemoryReader* reader, uintptr_t address, float* out_value);
int mrr_mem_read_f64(MRR_MemoryReader* reader, uintptr_t address, double* out_value);
int mrr_mem_read_byte(MRR_MemoryReader* reader, uintptr_t address, uint8_t* out_value);

/* String oku (null-terminated) */
int mrr_mem_read_string(MRR_MemoryReader* reader, uintptr_t address,
                        char* buffer, size_t max_len);

/* ═══════════════════════════════════════════════════════════
 * Pointer Zinciri (Multi-Level Pointer)
 * ═══════════════════════════════════════════════════════════ */

/*
 * Pointer chain takibi:
 *   base_address -> [base + offset[0]] -> [result + offset[1]] -> ... -> final_value
 *
 * Örnek: read_pointer_chain(base, {0x50, 0x14, 0x28}, 3, &result)
 *   1. ptr1 = *(base + 0x50)
 *   2. ptr2 = *(ptr1 + 0x14)
 *   3. result = ptr2 + 0x28  (son adres)
 */
int mrr_mem_read_pointer_chain(MRR_MemoryReader* reader,
                               uintptr_t base_address,
                               const intptr_t* offsets,
                               int offset_count,
                               uintptr_t* out_final_address);

/* ═══════════════════════════════════════════════════════════
 * Yardımcı Fonksiyonlar
 * ═══════════════════════════════════════════════════════════ */

/* Son hata mesajını al */
const char* mrr_mem_get_last_error(void);

/* Versiyonu al */
const char* mrr_mem_get_version(void);

#ifdef __cplusplus
}
#endif

#endif /* MRR_MEMORY_READER_H */
