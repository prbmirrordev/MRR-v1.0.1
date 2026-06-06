"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Memory Reader Bridge — Python ↔ C++ Köprüsü                ║
║                                                                  ║
║  memory_reader.dll/so'ya ctypes ile bağlanır.                   ║
║  Evaluator'a builtin fonksiyonlar olarak kaydedilir.            ║
║                                                                  ║
║  GÜVENLİK: Bu modül SADECE unsafe/exploit blokları              ║
║  içinden çağrılabilir.                                          ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import ctypes
import ctypes.util
import os
import sys
import struct
from typing import Optional, List, Dict, Any
from pathlib import Path


# ═══════════════════════════════════════════════════════════
# C Struct Tanımları (ctypes)
# ═══════════════════════════════════════════════════════════

class MRR_ProcessInfo(ctypes.Structure):
    _fields_ = [
        ("pid", ctypes.c_uint32),
        ("name", ctypes.c_char * 260),
    ]


class MRR_ModuleInfo(ctypes.Structure):
    _fields_ = [
        ("base_address", ctypes.c_size_t),
        ("size", ctypes.c_uint32),
        ("name", ctypes.c_char * 260),
        ("path", ctypes.c_char * 520),
    ]


class MRR_MemoryReader_C(ctypes.Structure):
    _fields_ = [
        ("native_handle", ctypes.c_void_p),
        ("pid", ctypes.c_uint32),
        ("is_attached", ctypes.c_int),
        ("process_name", ctypes.c_char * 260),
    ]


# ═══════════════════════════════════════════════════════════
# DLL/SO Yükleyici
# ═══════════════════════════════════════════════════════════

def _load_native_library() -> Optional[ctypes.CDLL]:
    """memory_reader native kütüphanesini yükle."""
    lib_dir = Path(__file__).parent.parent.parent / "library"

    if sys.platform == "win32":
        lib_name = "memory_reader.dll"
    else:
        lib_name = "libmemory_reader.so"

    lib_path = lib_dir / lib_name

    if lib_path.exists():
        try:
            return ctypes.CDLL(str(lib_path))
        except OSError as e:
            print(f"[MRR-MEM] Native kütüphane yüklenemedi: {e}")
            return None

    # Sistem yolunda ara
    found = ctypes.util.find_library("memory_reader")
    if found:
        return ctypes.CDLL(found)

    return None


# ═══════════════════════════════════════════════════════════
# Python Fallback (ctypes ile doğrudan Windows API)
# ═══════════════════════════════════════════════════════════

class MemoryReaderFallback:
    """
    Native DLL bulunamadığında Python ctypes ile doğrudan
    Windows API'yi kullanan yedek implementasyon.
    """

    def __init__(self):
        self._handle = None
        self._pid = 0
        self._process_name = ""

        if sys.platform != "win32":
            raise RuntimeError("Python fallback sadece Windows'ta desteklenir")

        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._psapi = ctypes.WinDLL("psapi", use_last_error=True)

    def attach_pid(self, pid: int) -> bool:
        PROCESS_VM_READ = 0x0010
        PROCESS_QUERY_INFORMATION = 0x0400

        self._handle = self._kernel32.OpenProcess(
            PROCESS_VM_READ | PROCESS_QUERY_INFORMATION,
            False,
            pid
        )

        if not self._handle:
            raise RuntimeError(
                f"OpenProcess başarısız (PID: {pid}): "
                f"Hata kodu {ctypes.get_last_error()}"
            )

        self._pid = pid
        return True

    def attach_name(self, name: str) -> bool:
        pid = self._find_process_by_name(name)
        if pid is None:
            raise RuntimeError(f"Process bulunamadı: {name}")
        return self.attach_pid(pid)

    def detach(self):
        if self._handle:
            self._kernel32.CloseHandle(self._handle)
            self._handle = None
            self._pid = 0

    def read_bytes(self, address: int, size: int) -> bytes:
        if not self._handle:
            raise RuntimeError("Process'e bağlı değil")

        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_size_t(0)

        success = self._kernel32.ReadProcessMemory(
            self._handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )

        if not success:
            raise RuntimeError(
                f"ReadProcessMemory başarısız (0x{address:X}): "
                f"Hata kodu {ctypes.get_last_error()}"
            )

        return buffer.raw[:bytes_read.value]

    def read_i32(self, address: int) -> int:
        data = self.read_bytes(address, 4)
        return struct.unpack('<i', data)[0]

    def read_i64(self, address: int) -> int:
        data = self.read_bytes(address, 8)
        return struct.unpack('<q', data)[0]

    def read_u32(self, address: int) -> int:
        data = self.read_bytes(address, 4)
        return struct.unpack('<I', data)[0]

    def read_u64(self, address: int) -> int:
        data = self.read_bytes(address, 8)
        return struct.unpack('<Q', data)[0]

    def read_f32(self, address: int) -> float:
        data = self.read_bytes(address, 4)
        return struct.unpack('<f', data)[0]

    def read_f64(self, address: int) -> float:
        data = self.read_bytes(address, 8)
        return struct.unpack('<d', data)[0]

    def read_string(self, address: int, max_len: int = 256) -> str:
        data = self.read_bytes(address, max_len)
        null_pos = data.find(b'\0')
        if null_pos >= 0:
            data = data[:null_pos]
        return data.decode('utf-8', errors='replace')

    def read_pointer_chain(self, base: int, offsets: list) -> int:
        current = base
        ptr_size = 8 if struct.calcsize('P') == 8 else 4

        for i, offset in enumerate(offsets):
            if i < len(offsets) - 1:
                # Dereference
                data = self.read_bytes(current + offset, ptr_size)
                if ptr_size == 8:
                    current = struct.unpack('<Q', data)[0]
                else:
                    current = struct.unpack('<I', data)[0]
                if current == 0:
                    raise RuntimeError(f"Null pointer: adım {i}")
            else:
                current += offset

        return current

    def get_module_base(self, module_name: str) -> int:
        if not self._handle:
            raise RuntimeError("Process'e bağlı değil")

        hMods = (ctypes.c_void_p * 1024)()
        cbNeeded = ctypes.c_ulong(0)

        self._psapi.EnumProcessModulesEx(
            self._handle, ctypes.byref(hMods),
            ctypes.sizeof(hMods), ctypes.byref(cbNeeded), 0x03
        )

        count = cbNeeded.value // ctypes.sizeof(ctypes.c_void_p)
        modName = ctypes.create_string_buffer(260)

        for i in range(count):
            self._psapi.GetModuleBaseNameA(
                self._handle, hMods[i], modName, 260
            )
            if modName.value.decode('utf-8', errors='replace').lower() == module_name.lower():
                class MODULEINFO(ctypes.Structure):
                    _fields_ = [
                        ("lpBaseOfDll", ctypes.c_void_p),
                        ("SizeOfImage", ctypes.c_ulong),
                        ("EntryPoint", ctypes.c_void_p),
                    ]
                mi = MODULEINFO()
                self._psapi.GetModuleInformation(
                    self._handle, hMods[i], ctypes.byref(mi),
                    ctypes.sizeof(mi)
                )
                return mi.lpBaseOfDll

        raise RuntimeError(f"Modül bulunamadı: {module_name}")

    def get_process_list(self) -> List[Dict[str, Any]]:
        TH32CS_SNAPPROCESS = 0x00000002

        class PROCESSENTRY32(ctypes.Structure):
            _fields_ = [
                ("dwSize", ctypes.c_ulong),
                ("cntUsage", ctypes.c_ulong),
                ("th32ProcessID", ctypes.c_ulong),
                ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
                ("th32ModuleID", ctypes.c_ulong),
                ("cntThreads", ctypes.c_ulong),
                ("th32ParentProcessID", ctypes.c_ulong),
                ("pcPriClassBase", ctypes.c_long),
                ("dwFlags", ctypes.c_ulong),
                ("szExeFile", ctypes.c_char * 260),
            ]

        snapshot = self._kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        pe32 = PROCESSENTRY32()
        pe32.dwSize = ctypes.sizeof(pe32)

        processes = []

        if self._kernel32.Process32First(snapshot, ctypes.byref(pe32)):
            while True:
                processes.append({
                    "pid": pe32.th32ProcessID,
                    "name": pe32.szExeFile.decode('utf-8', errors='replace')
                })
                if not self._kernel32.Process32Next(snapshot, ctypes.byref(pe32)):
                    break

        self._kernel32.CloseHandle(snapshot)
        return processes

    def _find_process_by_name(self, name: str) -> Optional[int]:
        for proc in self.get_process_list():
            if proc["name"].lower() == name.lower():
                return proc["pid"]
        return None


# ═══════════════════════════════════════════════════════════
# Birleşik API
# ═══════════════════════════════════════════════════════════

class MemoryReader:
    """
    MRR Memory Reader — Üst seviye API.
    
    Native DLL varsa onu kullanır, yoksa Python fallback'e döner.
    """

    def __init__(self):
        self._native = _load_native_library()
        self._fallback: Optional[MemoryReaderFallback] = None
        self._c_reader = None

        if self._native:
            self._setup_native()
        elif sys.platform == "win32":
            self._fallback = MemoryReaderFallback()

    def _setup_native(self):
        """Native C fonksiyon imzalarını tanımla."""
        lib = self._native

        lib.mrr_mem_attach_pid.argtypes = [ctypes.POINTER(MRR_MemoryReader_C), ctypes.c_uint32]
        lib.mrr_mem_attach_pid.restype = ctypes.c_int

        lib.mrr_mem_attach_name.argtypes = [ctypes.POINTER(MRR_MemoryReader_C), ctypes.c_char_p]
        lib.mrr_mem_attach_name.restype = ctypes.c_int

        lib.mrr_mem_detach.argtypes = [ctypes.POINTER(MRR_MemoryReader_C)]
        lib.mrr_mem_detach.restype = ctypes.c_int

        lib.mrr_mem_read_bytes.argtypes = [
            ctypes.POINTER(MRR_MemoryReader_C), ctypes.c_size_t,
            ctypes.c_void_p, ctypes.c_size_t, ctypes.POINTER(ctypes.c_size_t)
        ]
        lib.mrr_mem_read_bytes.restype = ctypes.c_int

        lib.mrr_mem_get_last_error.argtypes = []
        lib.mrr_mem_get_last_error.restype = ctypes.c_char_p

        self._c_reader = MRR_MemoryReader_C()

    def attach(self, target) -> 'MemoryReader':
        """Process'e bağlan. target: PID (int) veya isim (str)."""
        if self._fallback:
            if isinstance(target, int):
                self._fallback.attach_pid(target)
            else:
                self._fallback.attach_name(str(target))
        elif self._native:
            if isinstance(target, int):
                r = self._native.mrr_mem_attach_pid(ctypes.byref(self._c_reader), target)
            else:
                r = self._native.mrr_mem_attach_name(
                    ctypes.byref(self._c_reader), str(target).encode()
                )
            if r != 0:
                err = self._native.mrr_mem_get_last_error()
                raise RuntimeError(f"Bağlantı hatası: {err.decode() if err else 'bilinmiyor'}")
        else:
            raise RuntimeError("Memory reader mevcut değil (DLL ve fallback bulunamadı)")
        return self

    def detach(self):
        """Process bağlantısını kes."""
        if self._fallback:
            self._fallback.detach()
        elif self._native:
            self._native.mrr_mem_detach(ctypes.byref(self._c_reader))

    def read_i32(self, address: int) -> int:
        if self._fallback:
            return self._fallback.read_i32(address)
        val = ctypes.c_int32()
        self._native.mrr_mem_read_i32(ctypes.byref(self._c_reader), address, ctypes.byref(val))
        return val.value

    def read_i64(self, address: int) -> int:
        if self._fallback:
            return self._fallback.read_i64(address)
        val = ctypes.c_int64()
        self._native.mrr_mem_read_i64(ctypes.byref(self._c_reader), address, ctypes.byref(val))
        return val.value

    def read_f32(self, address: int) -> float:
        if self._fallback:
            return self._fallback.read_f32(address)
        val = ctypes.c_float()
        self._native.mrr_mem_read_f32(ctypes.byref(self._c_reader), address, ctypes.byref(val))
        return val.value

    def read_f64(self, address: int) -> float:
        if self._fallback:
            return self._fallback.read_f64(address)
        val = ctypes.c_double()
        self._native.mrr_mem_read_f64(ctypes.byref(self._c_reader), address, ctypes.byref(val))
        return val.value

    def read_string(self, address: int, max_len: int = 256) -> str:
        if self._fallback:
            return self._fallback.read_string(address, max_len)
        buf = ctypes.create_string_buffer(max_len)
        self._native.mrr_mem_read_string(ctypes.byref(self._c_reader), address, buf, max_len)
        return buf.value.decode('utf-8', errors='replace')

    def read_bytes(self, address: int, size: int) -> bytes:
        if self._fallback:
            return self._fallback.read_bytes(address, size)
        buf = ctypes.create_string_buffer(size)
        br = ctypes.c_size_t()
        self._native.mrr_mem_read_bytes(
            ctypes.byref(self._c_reader), address, buf, size, ctypes.byref(br)
        )
        return buf.raw[:br.value]

    def read_pointer_chain(self, base: int, offsets: list) -> int:
        if self._fallback:
            return self._fallback.read_pointer_chain(base, offsets)
        arr = (ctypes.c_ssize_t * len(offsets))(*offsets)
        result = ctypes.c_size_t()
        self._native.mrr_mem_read_pointer_chain(
            ctypes.byref(self._c_reader), base, arr, len(offsets), ctypes.byref(result)
        )
        return result.value

    def get_base_address(self, module_name: str) -> int:
        if self._fallback:
            return self._fallback.get_module_base(module_name)
        result = ctypes.c_size_t()
        r = self._native.mrr_mem_get_module_base(
            ctypes.byref(self._c_reader), module_name.encode(), ctypes.byref(result)
        )
        if r != 0:
            raise RuntimeError(f"Modül bulunamadı: {module_name}")
        return result.value

    def get_process_list(self) -> List[Dict[str, Any]]:
        if self._fallback:
            return self._fallback.get_process_list()
        procs = (MRR_ProcessInfo * 4096)()
        count = ctypes.c_int()
        self._native.mrr_mem_get_process_list(procs, 4096, ctypes.byref(count))
        return [{"pid": procs[i].pid, "name": procs[i].name.decode()} for i in range(count.value)]
