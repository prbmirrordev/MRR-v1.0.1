/*
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MRR Memory Reader — C++ Backend Implementation                 ║
 * ║                                                                  ║
 * ║  Cross-platform bellek okuma motoru:                            ║
 * ║    Windows: OpenProcess + ReadProcessMemory + ToolHelp32        ║
 * ║    Linux:   /proc/<pid>/mem + /proc/<pid>/maps                  ║
 * ║                                                                  ║
 * ║  Derleme (Windows MSVC):                                       ║
 * ║    cl /O2 /LD memory_reader.cpp /Fe:memory_reader.dll           ║
 * ║    /link psapi.lib advapi32.lib                                 ║
 * ║                                                                  ║
 * ║  Derleme (Linux GCC):                                          ║
 * ║    g++ -O2 -shared -fPIC memory_reader.cpp -o libmemory_reader.so ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

#include "memory_reader.h"
#include <cstring>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>

/* Thread-local hata mesajı */
static thread_local char g_last_error[512] = {0};

static void set_error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);
    vsnprintf(g_last_error, sizeof(g_last_error), fmt, args);
    va_end(args);
}

/* ═══════════════════════════════════════════════════════════
 * Platform-Specific Includes
 * ═══════════════════════════════════════════════════════════ */

#ifdef _WIN32
/* ── Windows Implementation ── */

#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <tlhelp32.h>
#include <psapi.h>
#include <stdarg.h>

#pragma comment(lib, "psapi.lib")
#pragma comment(lib, "advapi32.lib")

/* ─────────────────────────────────────────────────────
 * Process Keşfi — Windows
 * ───────────────────────────────────────────────────── */

int mrr_mem_get_process_list(MRR_ProcessInfo* out_list, int max_count, int* out_count) {
    if (!out_list || !out_count || max_count <= 0) {
        set_error("Geçersiz parametreler");
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        set_error("CreateToolhelp32Snapshot başarısız: %lu", GetLastError());
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    PROCESSENTRY32 pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32);
    *out_count = 0;

    if (Process32First(snapshot, &pe32)) {
        do {
            if (*out_count >= max_count) break;

            out_list[*out_count].pid = pe32.th32ProcessID;
            /* Windows uses wide chars in some configs, handle both */
            strncpy(out_list[*out_count].name, pe32.szExeFile, 259);
            out_list[*out_count].name[259] = '\0';
            (*out_count)++;
        } while (Process32Next(snapshot, &pe32));
    }

    CloseHandle(snapshot);
    return MRR_MEM_OK;
}

int mrr_mem_find_process_by_name(const char* name, uint32_t* out_pid) {
    if (!name || !out_pid) {
        set_error("Geçersiz parametreler");
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    HANDLE snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    if (snapshot == INVALID_HANDLE_VALUE) {
        set_error("Snapshot oluşturulamadı");
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    PROCESSENTRY32 pe32;
    pe32.dwSize = sizeof(PROCESSENTRY32);

    if (Process32First(snapshot, &pe32)) {
        do {
            if (_stricmp(pe32.szExeFile, name) == 0) {
                *out_pid = pe32.th32ProcessID;
                CloseHandle(snapshot);
                return MRR_MEM_OK;
            }
        } while (Process32Next(snapshot, &pe32));
    }

    CloseHandle(snapshot);
    set_error("Process bulunamadı: %s", name);
    return MRR_MEM_ERR_NOT_FOUND;
}

/* ─────────────────────────────────────────────────────
 * Process Bağlantısı — Windows
 * ───────────────────────────────────────────────────── */

int mrr_mem_attach_pid(MRR_MemoryReader* reader, uint32_t pid) {
    if (!reader) return MRR_MEM_ERR_INVALID_PARAM;

    memset(reader, 0, sizeof(MRR_MemoryReader));
    reader->pid = pid;

    HANDLE hProcess = OpenProcess(
        PROCESS_VM_READ | PROCESS_QUERY_INFORMATION | PROCESS_VM_OPERATION,
        FALSE,
        (DWORD)pid
    );

    if (!hProcess || hProcess == INVALID_HANDLE_VALUE) {
        set_error("OpenProcess başarısız (PID: %u): %lu", pid, GetLastError());
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    reader->native_handle = (void*)hProcess;
    reader->is_attached = 1;

    /* Process adını al */
    HMODULE hMod;
    DWORD cbNeeded;
    if (EnumProcessModules(hProcess, &hMod, sizeof(hMod), &cbNeeded)) {
        GetModuleBaseNameA(hProcess, hMod, reader->process_name, 259);
    }

    return MRR_MEM_OK;
}

int mrr_mem_attach_name(MRR_MemoryReader* reader, const char* process_name) {
    if (!reader || !process_name) return MRR_MEM_ERR_INVALID_PARAM;

    uint32_t pid = 0;
    int result = mrr_mem_find_process_by_name(process_name, &pid);
    if (result != MRR_MEM_OK) return result;

    return mrr_mem_attach_pid(reader, pid);
}

int mrr_mem_detach(MRR_MemoryReader* reader) {
    if (!reader) return MRR_MEM_ERR_INVALID_PARAM;

    if (reader->native_handle && reader->is_attached) {
        CloseHandle((HANDLE)reader->native_handle);
    }

    reader->native_handle = NULL;
    reader->is_attached = 0;
    return MRR_MEM_OK;
}

/* ─────────────────────────────────────────────────────
 * Modül Bilgisi — Windows
 * ───────────────────────────────────────────────────── */

int mrr_mem_get_module_base(MRR_MemoryReader* reader, const char* module_name,
                            uintptr_t* out_base) {
    if (!reader || !reader->is_attached || !module_name || !out_base) {
        set_error("Geçersiz parametreler veya bağlantı yok");
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    HANDLE hProcess = (HANDLE)reader->native_handle;
    HMODULE hMods[1024];
    DWORD cbNeeded;

    if (!EnumProcessModulesEx(hProcess, hMods, sizeof(hMods), &cbNeeded, LIST_MODULES_ALL)) {
        set_error("EnumProcessModulesEx başarısız: %lu", GetLastError());
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    int count = cbNeeded / sizeof(HMODULE);
    char modName[260];

    for (int i = 0; i < count; i++) {
        if (GetModuleBaseNameA(hProcess, hMods[i], modName, sizeof(modName))) {
            if (_stricmp(modName, module_name) == 0) {
                MODULEINFO modInfo;
                if (GetModuleInformation(hProcess, hMods[i], &modInfo, sizeof(modInfo))) {
                    *out_base = (uintptr_t)modInfo.lpBaseOfDll;
                    return MRR_MEM_OK;
                }
            }
        }
    }

    set_error("Modül bulunamadı: %s", module_name);
    return MRR_MEM_ERR_MODULE_NOT_FOUND;
}

int mrr_mem_get_module_list(MRR_MemoryReader* reader, MRR_ModuleInfo* out_list,
                            int max_count, int* out_count) {
    if (!reader || !reader->is_attached || !out_list || !out_count) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    HANDLE hProcess = (HANDLE)reader->native_handle;
    HMODULE hMods[1024];
    DWORD cbNeeded;

    if (!EnumProcessModulesEx(hProcess, hMods, sizeof(hMods), &cbNeeded, LIST_MODULES_ALL)) {
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    *out_count = 0;
    int count = cbNeeded / sizeof(HMODULE);

    for (int i = 0; i < count && *out_count < max_count; i++) {
        MODULEINFO modInfo;
        if (GetModuleInformation(hProcess, hMods[i], &modInfo, sizeof(modInfo))) {
            out_list[*out_count].base_address = (uintptr_t)modInfo.lpBaseOfDll;
            out_list[*out_count].size = modInfo.SizeOfImage;
            GetModuleBaseNameA(hProcess, hMods[i], out_list[*out_count].name, 259);
            GetModuleFileNameExA(hProcess, hMods[i], out_list[*out_count].path, 519);
            (*out_count)++;
        }
    }

    return MRR_MEM_OK;
}

/* ─────────────────────────────────────────────────────
 * Bellek Okuma — Windows
 * ───────────────────────────────────────────────────── */

int mrr_mem_read_bytes(MRR_MemoryReader* reader, uintptr_t address,
                       void* buffer, size_t size, size_t* bytes_read) {
    if (!reader || !reader->is_attached || !buffer) {
        set_error("Geçersiz okuma parametreleri");
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    SIZE_T nBytesRead = 0;
    BOOL success = ReadProcessMemory(
        (HANDLE)reader->native_handle,
        (LPCVOID)address,
        buffer,
        size,
        &nBytesRead
    );

    if (bytes_read) *bytes_read = (size_t)nBytesRead;

    if (!success) {
        set_error("ReadProcessMemory başarısız (Adres: 0x%llX): %lu",
                  (unsigned long long)address, GetLastError());
        return MRR_MEM_ERR_READ_FAILED;
    }

    return MRR_MEM_OK;
}

/* Tipli okuma makrosu */
#define IMPL_READ_TYPE(func_name, type)                                      \
int func_name(MRR_MemoryReader* reader, uintptr_t address, type* out_value) {\
    if (!out_value) return MRR_MEM_ERR_INVALID_PARAM;                        \
    return mrr_mem_read_bytes(reader, address, out_value, sizeof(type), NULL);\
}

IMPL_READ_TYPE(mrr_mem_read_i32,  int32_t)
IMPL_READ_TYPE(mrr_mem_read_i64,  int64_t)
IMPL_READ_TYPE(mrr_mem_read_u32,  uint32_t)
IMPL_READ_TYPE(mrr_mem_read_u64,  uint64_t)
IMPL_READ_TYPE(mrr_mem_read_f32,  float)
IMPL_READ_TYPE(mrr_mem_read_f64,  double)
IMPL_READ_TYPE(mrr_mem_read_byte, uint8_t)

int mrr_mem_read_string(MRR_MemoryReader* reader, uintptr_t address,
                        char* buffer, size_t max_len) {
    if (!reader || !reader->is_attached || !buffer || max_len == 0) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    /* Karakter karakter oku (null-terminator bulana kadar) */
    for (size_t i = 0; i < max_len - 1; i++) {
        char c;
        int result = mrr_mem_read_bytes(reader, address + i, &c, 1, NULL);
        if (result != MRR_MEM_OK) {
            buffer[i] = '\0';
            return result;
        }
        buffer[i] = c;
        if (c == '\0') return MRR_MEM_OK;
    }

    buffer[max_len - 1] = '\0';
    return MRR_MEM_OK;
}

/* ─────────────────────────────────────────────────────
 * Pointer Chain — Windows
 * ───────────────────────────────────────────────────── */

int mrr_mem_read_pointer_chain(MRR_MemoryReader* reader,
                               uintptr_t base_address,
                               const intptr_t* offsets,
                               int offset_count,
                               uintptr_t* out_final_address) {
    if (!reader || !reader->is_attached || !offsets || !out_final_address) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    uintptr_t current = base_address;

    for (int i = 0; i < offset_count; i++) {
        /* Son offset hariç, her adımda pointer dereference yap */
        if (i < offset_count - 1) {
            uintptr_t ptr_val = 0;

            /* Platform pointer boyutuna göre oku */
            #if defined(_WIN64) || defined(__x86_64__)
                int result = mrr_mem_read_bytes(reader, current + offsets[i],
                                                &ptr_val, sizeof(uint64_t), NULL);
            #else
                uint32_t ptr32 = 0;
                int result = mrr_mem_read_bytes(reader, current + offsets[i],
                                                &ptr32, sizeof(uint32_t), NULL);
                ptr_val = (uintptr_t)ptr32;
            #endif

            if (result != MRR_MEM_OK) {
                set_error("Pointer chain hatası: adım %d, adres 0x%llX + 0x%llX",
                          i, (unsigned long long)current,
                          (unsigned long long)offsets[i]);
                return result;
            }

            if (ptr_val == 0) {
                set_error("Null pointer: adım %d", i);
                return MRR_MEM_ERR_READ_FAILED;
            }

            current = ptr_val;
        } else {
            /* Son offset — sadece ekle, dereference yapma */
            current += offsets[i];
        }
    }

    *out_final_address = current;
    return MRR_MEM_OK;
}

#else
/* ═══════════════════════════════════════════════════════════
 * Linux Implementation
 * ═══════════════════════════════════════════════════════════ */

#include <dirent.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <stdarg.h>

int mrr_mem_get_process_list(MRR_ProcessInfo* out_list, int max_count, int* out_count) {
    if (!out_list || !out_count) return MRR_MEM_ERR_INVALID_PARAM;

    DIR* proc_dir = opendir("/proc");
    if (!proc_dir) return MRR_MEM_ERR_ACCESS_DENIED;

    *out_count = 0;
    struct dirent* entry;

    while ((entry = readdir(proc_dir)) != NULL && *out_count < max_count) {
        /* Sadece sayısal dizinler (PID'ler) */
        int is_pid = 1;
        for (int i = 0; entry->d_name[i]; i++) {
            if (entry->d_name[i] < '0' || entry->d_name[i] > '9') {
                is_pid = 0;
                break;
            }
        }
        if (!is_pid) continue;

        uint32_t pid = (uint32_t)atoi(entry->d_name);

        /* /proc/<pid>/comm dosyasından ismi oku */
        char comm_path[64];
        snprintf(comm_path, sizeof(comm_path), "/proc/%u/comm", pid);

        FILE* f = fopen(comm_path, "r");
        if (f) {
            out_list[*out_count].pid = pid;
            if (fgets(out_list[*out_count].name, 259, f)) {
                /* Yeni satır karakterini kaldır */
                size_t len = strlen(out_list[*out_count].name);
                if (len > 0 && out_list[*out_count].name[len-1] == '\n')
                    out_list[*out_count].name[len-1] = '\0';
            }
            fclose(f);
            (*out_count)++;
        }
    }

    closedir(proc_dir);
    return MRR_MEM_OK;
}

int mrr_mem_find_process_by_name(const char* name, uint32_t* out_pid) {
    MRR_ProcessInfo procs[2048];
    int count = 0;

    int result = mrr_mem_get_process_list(procs, 2048, &count);
    if (result != MRR_MEM_OK) return result;

    for (int i = 0; i < count; i++) {
        if (strcasecmp(procs[i].name, name) == 0) {
            *out_pid = procs[i].pid;
            return MRR_MEM_OK;
        }
    }

    set_error("Process bulunamadı: %s", name);
    return MRR_MEM_ERR_NOT_FOUND;
}

int mrr_mem_attach_pid(MRR_MemoryReader* reader, uint32_t pid) {
    if (!reader) return MRR_MEM_ERR_INVALID_PARAM;

    memset(reader, 0, sizeof(MRR_MemoryReader));
    reader->pid = pid;

    /* /proc/<pid>/mem erişim kontrolü */
    char mem_path[64];
    snprintf(mem_path, sizeof(mem_path), "/proc/%u/mem", pid);

    int fd = open(mem_path, O_RDONLY);
    if (fd < 0) {
        set_error("Process belleğine erişim başarısız (PID: %u)", pid);
        return MRR_MEM_ERR_ACCESS_DENIED;
    }

    reader->native_handle = (void*)(intptr_t)fd;
    reader->is_attached = 1;

    /* Process adını al */
    char comm_path[64];
    snprintf(comm_path, sizeof(comm_path), "/proc/%u/comm", pid);
    FILE* f = fopen(comm_path, "r");
    if (f) {
        if (fgets(reader->process_name, 259, f)) {
            size_t len = strlen(reader->process_name);
            if (len > 0 && reader->process_name[len-1] == '\n')
                reader->process_name[len-1] = '\0';
        }
        fclose(f);
    }

    return MRR_MEM_OK;
}

int mrr_mem_attach_name(MRR_MemoryReader* reader, const char* process_name) {
    if (!reader || !process_name) return MRR_MEM_ERR_INVALID_PARAM;

    uint32_t pid = 0;
    int result = mrr_mem_find_process_by_name(process_name, &pid);
    if (result != MRR_MEM_OK) return result;

    return mrr_mem_attach_pid(reader, pid);
}

int mrr_mem_detach(MRR_MemoryReader* reader) {
    if (!reader) return MRR_MEM_ERR_INVALID_PARAM;

    if (reader->is_attached && reader->native_handle) {
        close((int)(intptr_t)reader->native_handle);
    }

    reader->native_handle = NULL;
    reader->is_attached = 0;
    return MRR_MEM_OK;
}

int mrr_mem_get_module_base(MRR_MemoryReader* reader, const char* module_name,
                            uintptr_t* out_base) {
    if (!reader || !reader->is_attached || !module_name || !out_base) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    char maps_path[64];
    snprintf(maps_path, sizeof(maps_path), "/proc/%u/maps", reader->pid);

    FILE* f = fopen(maps_path, "r");
    if (!f) return MRR_MEM_ERR_ACCESS_DENIED;

    char line[512];
    while (fgets(line, sizeof(line), f)) {
        if (strstr(line, module_name)) {
            uintptr_t start;
            if (sscanf(line, "%lx-", &start) == 1) {
                *out_base = start;
                fclose(f);
                return MRR_MEM_OK;
            }
        }
    }

    fclose(f);
    set_error("Modül bulunamadı: %s", module_name);
    return MRR_MEM_ERR_MODULE_NOT_FOUND;
}

int mrr_mem_get_module_list(MRR_MemoryReader* reader, MRR_ModuleInfo* out_list,
                            int max_count, int* out_count) {
    if (!reader || !reader->is_attached || !out_list || !out_count) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    char maps_path[64];
    snprintf(maps_path, sizeof(maps_path), "/proc/%u/maps", reader->pid);

    FILE* f = fopen(maps_path, "r");
    if (!f) return MRR_MEM_ERR_ACCESS_DENIED;

    *out_count = 0;
    char line[512];

    while (fgets(line, sizeof(line), f) && *out_count < max_count) {
        uintptr_t start, end;
        char perms[5], path[520] = {0};

        if (sscanf(line, "%lx-%lx %4s %*s %*s %*s %519s", &start, &end, perms, path) >= 3) {
            if (path[0] == '/' && strstr(perms, "r")) {
                /* Aynı modülü tekrar ekleme */
                int duplicate = 0;
                for (int i = 0; i < *out_count; i++) {
                    if (strcmp(out_list[i].path, path) == 0) {
                        duplicate = 1;
                        break;
                    }
                }
                if (!duplicate) {
                    out_list[*out_count].base_address = start;
                    out_list[*out_count].size = (uint32_t)(end - start);
                    /* Yol'dan dosya adını çıkar */
                    const char* name = strrchr(path, '/');
                    strncpy(out_list[*out_count].name, name ? name + 1 : path, 259);
                    strncpy(out_list[*out_count].path, path, 519);
                    (*out_count)++;
                }
            }
        }
    }

    fclose(f);
    return MRR_MEM_OK;
}

int mrr_mem_read_bytes(MRR_MemoryReader* reader, uintptr_t address,
                       void* buffer, size_t size, size_t* bytes_read) {
    if (!reader || !reader->is_attached || !buffer) {
        return MRR_MEM_ERR_INVALID_PARAM;
    }

    int fd = (int)(intptr_t)reader->native_handle;
    ssize_t n = pread(fd, buffer, size, (off_t)address);

    if (n < 0) {
        set_error("pread başarısız (Adres: 0x%lx)", (unsigned long)address);
        return MRR_MEM_ERR_READ_FAILED;
    }

    if (bytes_read) *bytes_read = (size_t)n;
    return MRR_MEM_OK;
}

/* Tipli okuma makrosu */
#define IMPL_READ_TYPE(func_name, type)                                      \
int func_name(MRR_MemoryReader* reader, uintptr_t address, type* out_value) {\
    if (!out_value) return MRR_MEM_ERR_INVALID_PARAM;                        \
    return mrr_mem_read_bytes(reader, address, out_value, sizeof(type), NULL);\
}

IMPL_READ_TYPE(mrr_mem_read_i32,  int32_t)
IMPL_READ_TYPE(mrr_mem_read_i64,  int64_t)
IMPL_READ_TYPE(mrr_mem_read_u32,  uint32_t)
IMPL_READ_TYPE(mrr_mem_read_u64,  uint64_t)
IMPL_READ_TYPE(mrr_mem_read_f32,  float)
IMPL_READ_TYPE(mrr_mem_read_f64,  double)
IMPL_READ_TYPE(mrr_mem_read_byte, uint8_t)

int mrr_mem_read_string(MRR_MemoryReader* reader, uintptr_t address,
                        char* buffer, size_t max_len) {
    if (!reader || !reader->is_attached || !buffer || max_len == 0)
        return MRR_MEM_ERR_INVALID_PARAM;

    for (size_t i = 0; i < max_len - 1; i++) {
        char c;
        int result = mrr_mem_read_bytes(reader, address + i, &c, 1, NULL);
        if (result != MRR_MEM_OK) { buffer[i] = '\0'; return result; }
        buffer[i] = c;
        if (c == '\0') return MRR_MEM_OK;
    }
    buffer[max_len - 1] = '\0';
    return MRR_MEM_OK;
}

int mrr_mem_read_pointer_chain(MRR_MemoryReader* reader,
                               uintptr_t base_address,
                               const intptr_t* offsets,
                               int offset_count,
                               uintptr_t* out_final_address) {
    if (!reader || !reader->is_attached || !offsets || !out_final_address)
        return MRR_MEM_ERR_INVALID_PARAM;

    uintptr_t current = base_address;
    for (int i = 0; i < offset_count; i++) {
        if (i < offset_count - 1) {
            uintptr_t ptr_val = 0;
            int result = mrr_mem_read_bytes(reader, current + offsets[i],
                                            &ptr_val, sizeof(uintptr_t), NULL);
            if (result != MRR_MEM_OK) return result;
            if (ptr_val == 0) {
                set_error("Null pointer: adım %d", i);
                return MRR_MEM_ERR_READ_FAILED;
            }
            current = ptr_val;
        } else {
            current += offsets[i];
        }
    }
    *out_final_address = current;
    return MRR_MEM_OK;
}

#endif /* _WIN32 / Linux */

/* ═══════════════════════════════════════════════════════════
 * Ortak Yardımcı Fonksiyonlar
 * ═══════════════════════════════════════════════════════════ */

const char* mrr_mem_get_last_error(void) {
    return g_last_error;
}

const char* mrr_mem_get_version(void) {
    return "MRR-MemoryReader v1.0.0";
}
