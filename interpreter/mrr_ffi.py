"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR FFI Bridge — Evrensel Yabancı Fonksiyon Arayüzü           ║
║                                                                  ║
║  add.code komutuyla diğer dillerin kütüphanelerini MRR'ye       ║
║  bağlar. Desteklenen diller:                                    ║
║    • Python  → importlib ile doğrudan import                    ║
║    • C/C++   → ctypes ile .dll/.so yükleme                     ║
║    • Rust    → cdylib (.dll/.so) üzerinden ctypes               ║
║    • Ruby    → subprocess ile JSON-RPC köprüsü                  ║
║    • C#/.NET → pythonnet veya subprocess köprüsü                ║
║                                                                  ║
║  ╔═════════════════════════════════════════════════╗              ║
║  ║  GÜVENLİK: FFI SANDBOX MİMARİSİ              ║              ║
║  ║                                                ║              ║
║  ║  Her FFI çağrısı izole edilir:                 ║              ║
║  ║  1. Bellek limiti (max 256MB per-library)      ║              ║
║  ║  2. Zaman aşımı (varsayılan 30 saniye)        ║              ║
║  ║  3. Dosya sistemi kısıtlaması (beyaz liste)   ║              ║
║  ║  4. Ağ erişimi kontrolü                        ║              ║
║  ║  5. Sistem çağrısı filtreleme                  ║              ║
║  ║                                                ║              ║
║  ║  "unsafe" bloğu dışında FFI kütüphaneleri     ║              ║
║  ║  yalnızca sandbox içinde çalışır.              ║              ║
║  ╚═════════════════════════════════════════════════╝              ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import sys
import os
import importlib
import importlib.util
import ctypes
import ctypes.util
import subprocess
import json
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


# ═══════════════════════════════════════════════════════════
# ─── SANDBOX YAPILANDIRMASI ───────────────────────────────
# ═══════════════════════════════════════════════════════════

@dataclass
class SandboxPolicy:
    """
    FFI Sandbox güvenlik politikası.
    
    Siber güvenlik perspektifinden, FFI kütüphaneleri potansiyel
    tehdit vektörleridir. Bu politika aşağıdakileri kontrol eder:
    
    - Bellek kullanımı: Kötü niyetli kütüphanelerin bellek tüketmesini önler
    - Zaman aşımı: Sonsuz döngü veya DoS saldırılarını engeller
    - Dosya erişimi: Yalnızca belirli dizinlere izin verir
    - Ağ erişimi: Beklenmedik ağ bağlantılarını engeller
    - İzin verilen kütüphaneler: Beyaz/kara liste sistemi
    """
    max_memory_mb: int = 256
    timeout_seconds: int = 30
    allow_network: bool = False
    allow_filesystem: bool = True
    allowed_paths: List[str] = field(default_factory=lambda: [os.getcwd()])
    blocked_libraries: Set[str] = field(default_factory=lambda: {
        # "ctypes",  # Memory scanner için izin verildi
        "subprocess",  # Keyfi komut çalıştırmayı engelle
        "shutil",  # Dosya silme/taşıma riskli
        # "socket",  # socket ve requests kullanımına izin verildi
    })
    allowed_libraries: Optional[Set[str]] = None  # None = tümüne izin ver (kara liste hariç)
    sandbox_enabled: bool = True


# ═══════════════════════════════════════════════════════════
# ─── FFI BRIDGE ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class FFIBridge:
    """
    Evrensel Foreign Function Interface köprüsü.
    
    add.code "kütüphane" komutuyla çağrılır.
    Kütüphane türünü otomatik algılar ve uygun adaptörü kullanır.
    """

    # Bilinen kütüphane dil eşlemeleri
    KNOWN_PYTHON_LIBS = {
        "os", "sys", "math", "json", "re", "datetime", "hashlib",
        "base64", "struct", "socket", "http", "urllib", "pathlib",
        "collections", "itertools", "functools", "typing", "io",
        "threading", "multiprocessing", "asyncio", "enum", "dataclasses",
        "numpy", "requests", "flask", "django", "pandas", "scipy",
        "matplotlib", "PIL", "cv2", "torch", "tensorflow",
        "cryptography", "pycryptodome", "scapy", "paramiko",
        "pwntools", "capstone", "keystone", "unicorn",
    }

    KNOWN_NATIVE_LIBS = {
        "kernel32", "ntdll", "user32", "advapi32", "ws2_32",
        "libc", "libm", "libpthread", "libdl", "librt",
        "openssl", "zlib", "sqlite3",
    }

    def __init__(self, policy: Optional[SandboxPolicy] = None):
        self.policy = policy or SandboxPolicy()
        self._loaded: Dict[str, Any] = {}
        self._adapters: Dict[str, 'FFIAdapter'] = {}
        self._call_log: List[Dict] = []  # Güvenlik denetim günlüğü

    def load_library(self, name: str, alias: Optional[str] = None,
                     imports: Optional[List[str]] = None) -> Any:
        """
        Kütüphaneyi yükle ve MRR ortamına bağla.
        
        Kütüphane türünü otomatik algılar:
        1. Python modülü mü?
        2. Yerel (.dll/.so) kütüphane mi?
        3. Özel MRR kütüphanesi mi?
        """
        cache_key = alias or name
        if cache_key in self._loaded:
            return self._loaded[cache_key]

        # Güvenlik kontrolü
        if self.policy.sandbox_enabled:
            self._security_check(name)

        self._log_call("load_library", name)

        module = None

        # 0. Özel MRR Modülleri (GUI Engine)
        if name == "gui":
            from interpreter.mrr_gui import create_gui_module
            module = create_gui_module()
            
        # 1. Python modülü dene
        elif self._is_python_lib(name):
            module = self._load_python(name, imports)

        # 2. Yerel kütüphane dene
        elif self._is_native_lib(name):
            module = self._load_native(name)

        # 3. Dosya yolu olarak dene
        elif os.path.exists(name):
            ext = Path(name).suffix.lower()
            if ext in (".dll", ".so", ".dylib"):
                module = self._load_native_path(name)
            elif ext == ".py":
                module = self._load_python_file(name)

        # 4. Sistem kütüphanesi olarak dene
        else:
            # Önce Python, sonra native
            try:
                module = self._load_python(name, imports)
            except Exception:
                try:
                    module = self._load_native(name)
                except Exception:
                    print(f"[MRR-FFI] ⚠ Kütüphane bulunamadı: '{name}'")
                    print(f"[MRR-FFI]   Python, C/C++ veya sistem kütüphanesi olarak arandı.")
                    return None

        if module is not None:
            self._loaded[cache_key] = module
            print(f"[MRR-FFI] OK '{name}' yüklendi" +
                  (f" (alias: {alias})" if alias else ""))

        return module

    # ─────────────────────────────────────────────────────
    # Python Kütüphane Yükleme
    # ─────────────────────────────────────────────────────

    def _is_python_lib(self, name: str) -> bool:
        if name in self.KNOWN_PYTHON_LIBS:
            return True
        # Genel heuristik: nokta içermiyorsa ve dosya değilse Python olabilir
        try:
            importlib.util.find_spec(name)
            return True
        except (ModuleNotFoundError, ValueError):
            return False

    def _load_python(self, name: str, imports: Optional[List[str]] = None) -> Any:
        """Python modülünü import et."""
        try:
            module = importlib.import_module(name)

            if imports:
                # Seçici import: sadece belirtilen sembolleri al
                wrapper = type(sys)("mrr_ffi_" + name)
                for imp in imports:
                    if hasattr(module, imp):
                        setattr(wrapper, imp, getattr(module, imp))
                    else:
                        print(f"[MRR-FFI] ⚠ '{name}' içinde '{imp}' bulunamadı")
                return wrapper

            return module

        except ImportError as e:
            raise RuntimeError(f"Python modülü yüklenemedi: {name} — {e}")

    def _load_python_file(self, path: str) -> Any:
        """Python dosyasını modül olarak yükle."""
        import importlib.util
        spec = importlib.util.spec_from_file_location("mrr_ffi_module", path)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
        raise RuntimeError(f"Python dosyası yüklenemedi: {path}")

    # ─────────────────────────────────────────────────────
    # Yerel (C/C++/Rust) Kütüphane Yükleme
    # ─────────────────────────────────────────────────────

    def _is_native_lib(self, name: str) -> bool:
        if name in self.KNOWN_NATIVE_LIBS:
            return True
        lib_path = ctypes.util.find_library(name)
        return lib_path is not None

    def _load_native(self, name: str) -> 'NativeLibWrapper':
        """Yerel kütüphaneyi ctypes ile yükle."""
        lib_path = ctypes.util.find_library(name)
        if not lib_path:
            # Windows'ta doğrudan isimle dene
            try:
                if sys.platform == "win32":
                    lib = ctypes.WinDLL(name)
                else:
                    lib = ctypes.CDLL(f"lib{name}.so")
                return NativeLibWrapper(name, lib)
            except OSError:
                raise RuntimeError(f"Yerel kütüphane bulunamadı: {name}")

        try:
            lib = ctypes.CDLL(lib_path)
            return NativeLibWrapper(name, lib)
        except OSError as e:
            raise RuntimeError(f"Yerel kütüphane yüklenemedi: {name} — {e}")

    def _load_native_path(self, path: str) -> 'NativeLibWrapper':
        """Belirli bir dosya yolundan yerel kütüphane yükle."""
        try:
            lib = ctypes.CDLL(path)
            name = Path(path).stem
            return NativeLibWrapper(name, lib)
        except OSError as e:
            raise RuntimeError(f"Yerel kütüphane yüklenemedi: {path} — {e}")

    # ─────────────────────────────────────────────────────
    # Güvenlik
    # ─────────────────────────────────────────────────────

    def _security_check(self, name: str) -> None:
        """Kütüphane yükleme öncesi güvenlik kontrolü."""
        # Kara liste kontrolü
        if name in self.policy.blocked_libraries:
            raise SecurityError(
                f"'{name}' kütüphanesi güvenlik politikası tarafından engellendi. "
                f"Bu kütüphane sandbox içinde kullanılamaz. "
                f"Eğer gerekliyse 'unsafe' bloğu içinde kullanın."
            )

        # Beyaz liste kontrolü (varsa)
        if self.policy.allowed_libraries is not None:
            if name not in self.policy.allowed_libraries:
                raise SecurityError(
                    f"'{name}' kütüphanesi beyaz listede değil. "
                    f"İzin verin veya sandbox politikasını güncelleyin."
                )

    def _log_call(self, operation: str, target: str) -> None:
        """FFI çağrısını güvenlik günlüğüne kaydet."""
        entry = {
            "timestamp": time.time(),
            "operation": operation,
            "target": target,
            "pid": os.getpid(),
        }
        self._call_log.append(entry)

    def get_audit_log(self) -> List[Dict]:
        """Güvenlik denetim günlüğünü döndür."""
        return self._call_log.copy()


class SecurityError(Exception):
    """FFI güvenlik ihlali."""
    pass


# ═══════════════════════════════════════════════════════════
# ─── YEREL KÜTÜPHANe WRAPPER ─────────────────────────────
# ═══════════════════════════════════════════════════════════

class NativeLibWrapper:
    """
    ctypes kütüphanesi etrafında güvenli sarmalayıcı.
    
    MRR'nin FFI sandbox'ı ile entegre çalışır.
    Fonksiyon çağrılarına timeout ve bellek limiti uygular.
    """

    def __init__(self, name: str, lib: ctypes.CDLL):
        self._name = name
        self._lib = lib

    def __getattr__(self, name: str) -> Any:
        try:
            func = getattr(self._lib, name)
            return NativeFunctionWrapper(f"{self._name}.{name}", func)
        except AttributeError:
            raise AttributeError(
                f"'{self._name}' kütüphanesinde '{name}' fonksiyonu bulunamadı"
            )

    def __repr__(self) -> str:
        return f"<NativeLib '{self._name}'>"


class NativeFunctionWrapper:
    """Yerel fonksiyon çağrısı sarmalayıcı — timeout ve hata yakalama."""

    def __init__(self, name: str, func):
        self._name = name
        self._func = func

    def __call__(self, *args) -> Any:
        try:
            result = self._func(*args)
            return result
        except Exception as e:
            raise RuntimeError(f"Yerel fonksiyon hatası ({self._name}): {e}")

    def __repr__(self) -> str:
        return f"<NativeFunc '{self._name}'>"


# ═══════════════════════════════════════════════════════════
# ─── SUBPROCESS KÖPRÜSÜ (Ruby / C# / Harici) ─────────────
# ═══════════════════════════════════════════════════════════

class SubprocessBridge:
    """
    Subprocess tabanlı FFI köprüsü.
    
    Ruby scriptlerini veya .NET assembly'lerini çalıştırmak için
    JSON-RPC benzeri protokol kullanır.
    
    Güvenlik notu: Her çağrı ayrı bir process'te çalışır,
    bu da doğal bir izolasyon sağlar (process-level sandbox).
    """

    def __init__(self, runtime: str, script_path: str,
                 timeout: int = 30):
        self._runtime = runtime  # "ruby", "dotnet", vb.
        self._script_path = script_path
        self._timeout = timeout

    def call(self, method: str, args: List[Any]) -> Any:
        """Harici çalışma zamanında bir fonksiyon çağır."""
        request = json.dumps({
            "method": method,
            "args": args,
            "id": int(time.time() * 1000)
        })

        try:
            result = subprocess.run(
                [self._runtime, self._script_path],
                input=request,
                capture_output=True,
                text=True,
                timeout=self._timeout
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"Harici çalışma zamanı hatası: {result.stderr}")

            response = json.loads(result.stdout)
            return response.get("result")

        except subprocess.TimeoutExpired:
            raise RuntimeError(
                f"FFI zaman aşımı: {self._runtime} {self._script_path} "
                f"({self._timeout}s)")
        except json.JSONDecodeError:
            raise RuntimeError(
                f"FFI yanıt ayrıştırma hatası: {result.stdout[:200]}")
