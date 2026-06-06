"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Evaluator — AST Yorumlayıcı (Interpreter Engine)          ║
║                                                                  ║
║  Oluşturulan AST'yi anında bellekte işleyip çalıştırır.         ║
║  .exe derlemesi gerektirmeden kodu çalıştırır.                  ║
║                                                                  ║
║  Özellikler:                                                    ║
║    - Değişken bağlama ve kapsam yönetimi                        ║
║    - Fonksiyon tanımlama ve çağrısı                             ║
║    - Kontrol akışı (if/elif/else, for, while, match)            ║
║    - Struct / Class örnekleme                                    ║
║    - FFI entegrasyonu (add.code ile yüklenen kütüphaneler)      ║
║    - Sandbox: FFI çağrılarını izole eder                        ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import sys
import os
import re
import time
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from interpreter.mrr_parser import (
    ASTNode, Program, LiteralExpr, IdentifierExpr, BinaryExpr, UnaryExpr,
    CallExpr, MemberAccessExpr, IndexExpr, CastExpr, RangeExpr, ListExpr,
    DictExpr, TupleExpr, LambdaExpr, AwaitExpr, AsmExpr, ShellcodeExpr,
    TernaryExpr, PipeExpr, AssignExpr, FunctionDecl, VarDecl,
    AddCodeDecl, ModuleDecl, UseDecl, StructDecl, ClassDecl,
    TraitDecl, ImplDecl, ExploitDecl, DriverDecl, HookDecl, IfStmt,
    ForStmt, WhileStmt, LoopStmt, MatchStmt, ReturnStmt, BreakStmt,
    ContinueStmt, PassStmt, UnsafeBlock, KernelBlock, ExpressionStmt,
    PrintStmt, Parameter, TryCatchStmt, ThrowStmt, EnumDecl,
    DeleteStmt, DoWhileStmt, DeferStmt
)


# ═══════════════════════════════════════════════════════════
# ─── ÇALIŞMA ZAMANI DEĞERLERİ ─────────────────────────────
# ═══════════════════════════════════════════════════════════

class MRRBreak(Exception):
    """Break deyimi için sinyal."""
    pass

class MRRContinue(Exception):
    """Continue deyimi için sinyal."""
    pass

class MRRReturn(Exception):
    """Return deyimi için sinyal."""
    def __init__(self, value: Any = None):
        self.value = value

class MRRRuntimeError(Exception):
    """Çalışma zamanı hatası."""
    def __init__(self, message: str, location=None):
        self.location = location
        super().__init__(f"[Çalışma Zamanı Hatası] {location}: {message}" if location
                         else f"[Çalışma Zamanı Hatası] {message}")


class MRRTemporalVar:
    """Zaman Yolculuğu (Time-Travel) Debugging için geçmişi tutan değişken sarmalayıcı."""
    def __init__(self, value: Any, max_history: int = 10):
        self.history = []
        self.value = value
        self.max_history = max_history

    def set(self, new_value: Any) -> None:
        self.history.append(self.value)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.value = new_value

    def rollback(self, steps: int) -> None:
        for _ in range(steps):
            if self.history:
                self.value = self.history.pop()


class MRRUntrustedString:
    """SecTypes: Güvenilmeyen (Untrusted) kullanıcı veya ağ verisi."""
    def __init__(self, value: str):
        self.value = value

    def __str__(self):
        return str(self.value)

    def __repr__(self):
        return f"Untrusted({self.value!r})"

    def __add__(self, other):
        if isinstance(other, MRRUntrustedString):
            return MRRUntrustedString(self.value + other.value)
        return MRRUntrustedString(self.value + str(other))

    def __radd__(self, other):
        return MRRUntrustedString(str(other) + self.value)


@dataclass
class MRRFunction:
    """MRR fonksiyon nesnesi."""
    name: str
    params: List[Parameter]
    body: List[ASTNode]
    closure: 'Environment'
    return_type: Optional[str] = None
    is_builtin: bool = False
    builtin_fn: Optional[Callable] = None
    is_async: bool = False


@dataclass
class MRRStruct:
    """MRR struct tipi."""
    name: str
    fields: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        fields_str = ", ".join(f"{k}={v!r}" for k, v in self.fields.items())
        return f"{self.name}({fields_str})"


@dataclass
class MRRClass:
    """MRR sınıf tipi."""
    name: str
    bases: List[str] = field(default_factory=list)
    methods: Dict[str, MRRFunction] = field(default_factory=dict)
    static_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MRRInstance:
    """MRR sınıf örneği."""
    class_ref: MRRClass
    fields: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:
        return f"<{self.class_ref.name} instance>"


class MRRPointer:
    """Unsafe pointer / raw memory nesnesi."""
    def __init__(self, buffer: Optional[bytearray] = None,
                 offset: int = 0, element_type: str = "byte",
                 address: int = 0):
        self.buffer = buffer if buffer is not None else bytearray()
        self.offset = int(offset)
        self.element_type = element_type
        self.address = int(address)
        self.freed = False

    def _element_size(self) -> int:
        sizes = {
            "byte": 1, "u8": 1, "i8": 1,
            "u16": 2, "i16": 2,
            "u32": 4, "i32": 4,
            "u64": 8, "i64": 8,
            "usize": 8, "isize": 8,
        }
        if self.element_type.startswith("ptr<") and self.element_type.endswith(">"):
            inner = self.element_type[4:-1]
            return sizes.get(inner, 8)
        return sizes.get(self.element_type, 8)

    def read(self, size: Optional[int] = None) -> Any:
        if self.freed:
            raise MRRRuntimeError("Serbest bırakılmış pointer üzerinden okuma")
        size = int(size) if size is not None else self._element_size()
        if self.buffer and self.offset + size <= len(self.buffer):
            chunk = self.buffer[self.offset:self.offset + size]
            if size == 1:
                return chunk[0]
            signed = self.element_type.startswith("i")
            return int.from_bytes(chunk, "little", signed=signed)
        if self.address:
            return self.address
        return 0

    def write(self, value: Any) -> None:
        if self.freed:
            raise MRRRuntimeError("Serbest bırakılmış pointer üzerine yazma")
        if isinstance(value, int):
            size = self._element_size()
            data = int(value).to_bytes(size, "little", signed=self.element_type.startswith("i"))
        elif isinstance(value, (bytes, bytearray)):
            data = bytes(value)
        else:
            data = str(value).encode("utf-8")

        end = self.offset + len(data)
        if end > len(self.buffer):
            self.buffer.extend(b"\x00" * (end - len(self.buffer)))
        self.buffer[self.offset:end] = data

    def offset(self, delta: Any) -> "MRRPointer":
        delta_value = int(delta)
        step = self._element_size()
        return MRRPointer(buffer=self.buffer, offset=self.offset + delta_value * step,
                          element_type=self.element_type,
                          address=self.address + delta_value * step)

    def as_type(self, target_type: str) -> "MRRPointer":
        return MRRPointer(buffer=self.buffer, offset=self.offset,
                          element_type=target_type, address=self.address)

    def len(self) -> int:
        if self.freed:
            return 0
        return max(0, len(self.buffer) - self.offset)

    def free(self) -> None:
        self.buffer = bytearray()
        self.freed = True

    def __len__(self) -> int:
        return self.len()

    def __repr__(self) -> str:
        return f"MRRPointer(type={self.element_type}, offset={self.offset}, len={self.len()})"


class MRRFuture:
    """Basit async/future desteği."""
    def __init__(self, evaluator: 'Evaluator', func: 'MRRFunction', args: List[Any], env: 'Environment'):
        self.evaluator = evaluator
        self.func = func
        self.args = args
        self.env = env
        self._result: Any = None
        self._finished = False

    def result(self) -> Any:
        if not self._finished:
            self._result = self.evaluator._call_function(self.func, self.args, self.env)
            self._finished = True
        return self._result

    def __repr__(self) -> str:
        return f"MRRFuture(finished={self._finished})"


class MRRShellcode:
    """Shellcode payload representation for interpreter mode."""

    def __init__(self, arch: str, code: str):
        self.arch = arch
        self.code = code
        self.data = self._assemble(code)

    def _assemble(self, code: str) -> bytes:
        output = bytearray()
        for raw_line in code.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            if line.startswith("db "):
                entries = [item.strip() for item in line[3:].split(",")]
                for entry in entries:
                    if entry.startswith('"') and entry.endswith('"'):
                        output.extend(entry[1:-1].encode("utf-8"))
                    elif entry.startswith("'") and entry.endswith("'") and len(entry) == 3:
                        output.append(ord(entry[1]))
                    else:
                        try:
                            output.append(int(entry, 0) & 0xFF)
                        except Exception:
                            output.extend(entry.encode("utf-8"))
            else:
                output.extend(line.encode("utf-8"))
        return bytes(output)

    def len(self) -> int:
        return len(self.data)

    def __len__(self) -> int:
        return len(self.data)

    def __repr__(self) -> str:
        return f"<shellcode arch={self.arch} size={len(self.data)}>"


# ═══════════════════════════════════════════════════════════
# ─── ORTAM / KAPSAM (Environment) ─────────────────────────
# ═══════════════════════════════════════════════════════════

class Environment:
    """
    İç içe kapsamları destekleyen ortam (scope chain).
    Her blok kendi kapsamını oluşturur; dışarıdaki değişkenlere
    parent zinciri üzerinden erişilir.
    """

    def __init__(self, parent: Optional['Environment'] = None,
                 name: str = "global"):
        self.parent = parent
        self.name = name
        self._vars: Dict[str, Any] = {}
        self._mutables: set = set()  # Değiştirilebilir değişkenler

    def define(self, name: str, value: Any, mutable: bool = False) -> None:
        self._vars[name] = value
        if mutable:
            self._mutables.add(name)

    def register_defer(self, callback: Callable[[], Any]) -> None:
        if not hasattr(self, 'deferred'):
            self.deferred = []
        self.deferred.append(callback)

    def run_deferred(self) -> None:
        if hasattr(self, 'deferred'):
            while self.deferred:
                callback = self.deferred.pop()
                callback()

    def get(self, name: str) -> Any:
        raw = self.get_raw(name)
        if isinstance(raw, MRRTemporalVar):
            return raw.value
        return raw

    def get_raw(self, name: str) -> Any:
        if name in self._vars:
            return self._vars[name]
        if self.parent:
            return self.parent.get_raw(name)
        raise MRRRuntimeError(f"Tanımsız değişken: '{name}'")

    def set(self, name: str, value: Any) -> None:
        if name in self._vars:
            if name not in self._mutables:
                raise MRRRuntimeError(
                    f"'{name}' değiştirilemez (immutable). "
                    f"'mut' ile tanımlayın.")
            
            raw = self._vars[name]
            if isinstance(raw, MRRTemporalVar):
                raw.set(value)
            else:
                self._vars[name] = value
            return
        if self.parent and self.parent.has(name):
            self.parent.set(name, value)
            return
        self.define(name, value, mutable=True)

    def has(self, name: str) -> bool:
        if name in self._vars:
            return True
        if self.parent:
            return self.parent.has(name)
        return False

    def child(self, name: str = "block") -> 'Environment':
        return Environment(parent=self, name=name)


# ═══════════════════════════════════════════════════════════
# ─── EVALUATOR (YORUMLAYICI) ──────────────────────────────
# ═══════════════════════════════════════════════════════════

class Evaluator:
    """
    MRR AST Evaluator — Tree-Walking Interpreter.
    
    AST'yi dolaşarak her düğümü anında çalıştırır.
    Performans-kritik olmayan kod için ideal;
    Phase 3'te JIT desteği eklenecek.
    """

    def __init__(self):
        self.global_env = Environment(name="global")
        self.ffi_bridge: Optional[Any] = None  # FFIBridge referansı
        self._loaded_libs: Dict[str, Any] = {}
        self._setup_builtins()
        self._start_time = time.time()

    # ─────────────────────────────────────────────────────
    # Yerleşik (Built-in) Fonksiyonlar
    # ─────────────────────────────────────────────────────

    def _setup_builtins(self) -> None:
        """Yerleşik fonksiyonları global ortama ekle."""

        # I/O
        self._define_builtin("print", self._builtin_print)
        self._define_builtin("println", self._builtin_println)
        self._define_builtin("input", self._builtin_input)

        # Tip dönüşümleri
        self._define_builtin("integer", self._builtin_integer)
        self._define_builtin("float", lambda args: float(args[0]) if args else 0.0)
        self._define_builtin("str", lambda args: str(args[0]) if args else "")
        self._define_builtin("bool", lambda args: bool(args[0]) if args else False)
        self._define_builtin("byte", lambda args: int(args[0]) & 0xFF if args else 0)
        self._define_builtin("alloc", self._builtin_alloc)
        self._define_builtin("free", self._builtin_free)
        self._define_builtin("drop", self._builtin_free)
        self._define_builtin("volatile", lambda args: args[0] if args else None)

        # Koleksiyonlar
        self._define_builtin("len", lambda args: len(args[0]) if args else 0)
        self._define_builtin("range", self._builtin_range)
        self._define_builtin("append", lambda args: args[0].append(args[1]) if len(args) >= 2 else None)
        self._define_builtin("pop", lambda args: args[0].pop() if args else None)

        # Matematik
        self._define_builtin("abs", lambda args: abs(args[0]) if args else 0)
        self._define_builtin("min", lambda args: min(*args) if args else 0)
        self._define_builtin("max", lambda args: max(*args) if args else 0)

        # Sistem
        self._define_builtin("typeof", lambda args: type(args[0]).__name__ if args else "void")
        self._define_builtin("sizeof", self._builtin_sizeof)
        self._define_builtin("exit", lambda args: sys.exit(int(args[0]) if args else 0))
        self._define_builtin("time", lambda args: time.time())
        self._define_builtin("system", self._builtin_system)
        
        # SecTypes
        self._define_builtin("sanitize", lambda args: str(args[0].value) if isinstance(args[0], MRRUntrustedString) else str(args[0]) if args else "")

        # Hex/Binary yardımcıları
        self._define_builtin("hex", lambda args: hex(int(args[0])) if args else "0x0")
        self._define_builtin("bin", lambda args: bin(int(args[0])) if args else "0b0")
        self._define_builtin("oct", lambda args: oct(int(args[0])) if args else "0o0")

        # ── Yeni: String İşlemleri ──
        self._define_builtin("split", lambda args: args[0].split(args[1] if len(args) > 1 else None) if args else [])
        self._define_builtin("join", lambda args: str(args[0]).join(args[1]) if len(args) >= 2 else "")
        self._define_builtin("replace", lambda args: args[0].replace(args[1], args[2]) if len(args) >= 3 else args[0] if args else "")
        self._define_builtin("upper", lambda args: str(args[0]).upper() if args else "")
        self._define_builtin("lower", lambda args: str(args[0]).lower() if args else "")
        self._define_builtin("trim", lambda args: str(args[0]).strip() if args else "")
        self._define_builtin("contains", lambda args: args[1] in args[0] if len(args) >= 2 else False)
        self._define_builtin("starts_with", lambda args: str(args[0]).startswith(str(args[1])) if len(args) >= 2 else False)
        self._define_builtin("ends_with", lambda args: str(args[0]).endswith(str(args[1])) if len(args) >= 2 else False)
        self._define_builtin("format", self._builtin_format)
        self._define_builtin("chr", lambda args: chr(int(args[0])) if args else "")
        self._define_builtin("ord", lambda args: ord(str(args[0])[0]) if args and len(str(args[0])) > 0 else 0)

        # ── Yeni: Koleksiyon İşlemleri ──
        self._define_builtin("reverse", lambda args: list(reversed(args[0])) if isinstance(args[0], list) else str(args[0])[::-1] if args else [])
        self._define_builtin("sort", lambda args: sorted(args[0]) if args else [])
        self._define_builtin("map", self._builtin_map)
        self._define_builtin("filter", self._builtin_filter)
        self._define_builtin("reduce", self._builtin_reduce)
        self._define_builtin("enumerate", lambda args: list(enumerate(args[0])) if args else [])
        self._define_builtin("zip", lambda args: list(zip(args[0], args[1])) if len(args) >= 2 else [])
        self._define_builtin("keys", lambda args: list(args[0].keys()) if args and isinstance(args[0], dict) else [])
        self._define_builtin("values", lambda args: list(args[0].values()) if args and isinstance(args[0], dict) else [])
        self._define_builtin("items", lambda args: list(args[0].items()) if args and isinstance(args[0], dict) else [])
        self._define_builtin("has_key", lambda args: args[1] in args[0] if len(args) >= 2 and isinstance(args[0], dict) else False)
        self._define_builtin("insert", lambda args: args[0].insert(int(args[1]), args[2]) if len(args) >= 3 else None)
        self._define_builtin("remove", lambda args: args[0].remove(args[1]) if len(args) >= 2 else None)
        self._define_builtin("slice", lambda args: args[0][int(args[1]):int(args[2])] if len(args) >= 3 else args[0] if args else [])
        self._define_builtin("flat", lambda args: [item for sublist in args[0] for item in (sublist if isinstance(sublist, list) else [sublist])] if args else [])

        # ── Yeni: Matematik ──
        self._define_builtin("round", lambda args: round(args[0], int(args[1]) if len(args) > 1 else 0) if args else 0)
        self._define_builtin("pow", lambda args: args[0] ** args[1] if len(args) >= 2 else 0)
        self._define_builtin("sqrt", lambda args: args[0] ** 0.5 if args else 0.0)

        # ── Yeni: Sistem ──
        self._define_builtin("sleep", lambda args: time.sleep(float(args[0])) if args else None)
        self._define_builtin("random_int", lambda args: random.randint(int(args[0]), int(args[1])) if len(args) >= 2 else random.randint(0, 100))
        self._define_builtin("assert", self._builtin_assert)
        self._define_builtin("type_name", self._builtin_type_name)
        self._define_builtin("hash", lambda args: hash(args[0]) if args else 0)
        self._define_builtin("id", lambda args: id(args[0]) if args else 0)

        # ── Dosya I/O ──
        self._define_builtin("readfile", self._builtin_readfile)
        self._define_builtin("writefile", self._builtin_writefile)

        # ── Gelişmiş Dosya I/O ──
        self._define_builtin("file_read_lines", self._builtin_file_read_lines)
        self._define_builtin("file_append", self._builtin_file_append)
        self._define_builtin("file_exists", lambda args: os.path.exists(str(args[0])) if args else False)
        self._define_builtin("file_delete", self._builtin_file_delete)
        self._define_builtin("file_copy", self._builtin_file_copy)
        self._define_builtin("file_size", lambda args: os.path.getsize(str(args[0])) if args and os.path.exists(str(args[0])) else -1)
        self._define_builtin("file_rename", lambda args: os.rename(str(args[0]), str(args[1])) if len(args) >= 2 else None)

        # ── Dizin İşlemleri ──
        self._define_builtin("dir_list", self._builtin_dir_list)
        self._define_builtin("dir_create", self._builtin_dir_create)
        self._define_builtin("dir_exists", lambda args: os.path.isdir(str(args[0])) if args else False)
        self._define_builtin("path_join", lambda args: os.path.join(*[str(a) for a in args]) if args else "")
        self._define_builtin("path_dirname", lambda args: os.path.dirname(str(args[0])) if args else "")
        self._define_builtin("path_basename", lambda args: os.path.basename(str(args[0])) if args else "")
        self._define_builtin("path_ext", lambda args: os.path.splitext(str(args[0]))[1] if args else "")
        self._define_builtin("cwd", lambda args: os.getcwd())

        # ── Gelişmiş String Manipülasyonu ──
        self._define_builtin("pad_left", lambda args: str(args[0]).rjust(int(args[1]), str(args[2]) if len(args) > 2 else ' ') if len(args) >= 2 else str(args[0]) if args else "")
        self._define_builtin("pad_right", lambda args: str(args[0]).ljust(int(args[1]), str(args[2]) if len(args) > 2 else ' ') if len(args) >= 2 else str(args[0]) if args else "")
        self._define_builtin("substring", lambda args: str(args[0])[int(args[1]):int(args[2])] if len(args) >= 3 else str(args[0])[int(args[1]):] if len(args) >= 2 else str(args[0]) if args else "")
        self._define_builtin("char_at", lambda args: str(args[0])[int(args[1])] if len(args) >= 2 and int(args[1]) < len(str(args[0])) else "")
        self._define_builtin("index_of", lambda args: str(args[0]).find(str(args[1])) if len(args) >= 2 else -1)
        self._define_builtin("last_index_of", lambda args: str(args[0]).rfind(str(args[1])) if len(args) >= 2 else -1)
        self._define_builtin("repeat", lambda args: str(args[0]) * int(args[1]) if len(args) >= 2 else str(args[0]) if args else "")
        self._define_builtin("is_numeric", lambda args: str(args[0]).isnumeric() if args else False)
        self._define_builtin("is_alpha", lambda args: str(args[0]).isalpha() if args else False)
        self._define_builtin("is_alnum", lambda args: str(args[0]).isalnum() if args else False)
        self._define_builtin("is_space", lambda args: str(args[0]).isspace() if args else False)
        self._define_builtin("capitalize", lambda args: str(args[0]).capitalize() if args else "")
        self._define_builtin("title_case", lambda args: str(args[0]).title() if args else "")
        self._define_builtin("count", lambda args: str(args[0]).count(str(args[1])) if len(args) >= 2 else 0)
        self._define_builtin("lstrip", lambda args: str(args[0]).lstrip(str(args[1]) if len(args) > 1 else None) if args else "")
        self._define_builtin("rstrip", lambda args: str(args[0]).rstrip(str(args[1]) if len(args) > 1 else None) if args else "")
        self._define_builtin("center", lambda args: str(args[0]).center(int(args[1]), str(args[2]) if len(args) > 2 else ' ') if len(args) >= 2 else str(args[0]) if args else "")
        self._define_builtin("zfill", lambda args: str(args[0]).zfill(int(args[1])) if len(args) >= 2 else str(args[0]) if args else "")

        # ── Regex ──
        self._define_builtin("regex_match", self._builtin_regex_match)
        self._define_builtin("regex_find_all", self._builtin_regex_find_all)
        self._define_builtin("regex_replace", self._builtin_regex_replace)
        self._define_builtin("regex_split", lambda args: re.split(str(args[0]), str(args[1])) if len(args) >= 2 else [])

        # ── Encoding ──
        self._define_builtin("encode_base64", self._builtin_encode_base64)
        self._define_builtin("decode_base64", self._builtin_decode_base64)
        self._define_builtin("encode_url", self._builtin_encode_url)
        self._define_builtin("decode_url", self._builtin_decode_url)
        self._define_builtin("encode_hex", lambda args: str(args[0]).encode().hex() if args else "")
        self._define_builtin("decode_hex", lambda args: bytes.fromhex(str(args[0])).decode('utf-8', errors='replace') if args else "")

        # ── Gelişmiş Array/Koleksiyon ──
        self._define_builtin("find", self._builtin_find)
        self._define_builtin("find_index", self._builtin_find_index)
        self._define_builtin("every", self._builtin_every)
        self._define_builtin("some", self._builtin_some)
        self._define_builtin("unique", lambda args: list(dict.fromkeys(args[0])) if args else [])
        self._define_builtin("chunk", self._builtin_chunk)
        self._define_builtin("flatten", lambda args: self._flatten_list(args[0]) if args else [])
        self._define_builtin("group_by", self._builtin_group_by)
        self._define_builtin("sum", lambda args: sum(args[0]) if args and isinstance(args[0], list) else sum(args))
        self._define_builtin("any", lambda args: any(args[0]) if args else False)
        self._define_builtin("all", lambda args: all(args[0]) if args else True)
        self._define_builtin("count_if", self._builtin_count_if)
        self._define_builtin("take", lambda args: list(args[0])[:int(args[1])] if len(args) >= 2 else list(args[0]) if args else [])
        self._define_builtin("drop", lambda args: list(args[0])[int(args[1]):] if len(args) >= 2 else [] if args else [])
        self._define_builtin("zip_with", self._builtin_zip_with)

        # ── Tarih ve Saat ──
        self._define_builtin("now", lambda args: time.time())
        self._define_builtin("now_str", self._builtin_now_str)
        self._define_builtin("date_format", self._builtin_date_format)
        self._define_builtin("date_parse", self._builtin_date_parse)
        self._define_builtin("date_diff", lambda args: float(args[0]) - float(args[1]) if len(args) >= 2 else 0.0)
        self._define_builtin("date_add", lambda args: float(args[0]) + float(args[1]) if len(args) >= 2 else float(args[0]) if args else 0.0)
        self._define_builtin("date_year", self._builtin_date_component("tm_year"))
        self._define_builtin("date_month", self._builtin_date_component("tm_mon"))
        self._define_builtin("date_day", self._builtin_date_component("tm_mday"))
        self._define_builtin("date_hour", self._builtin_date_component("tm_hour"))
        self._define_builtin("date_minute", self._builtin_date_component("tm_min"))
        self._define_builtin("date_second", self._builtin_date_component("tm_sec"))
        self._define_builtin("date_weekday", self._builtin_date_component("tm_wday"))
        self._define_builtin("date_is_leap_year", lambda args: self._is_leap_year(int(args[0])) if args else False)
        self._define_builtin("stopwatch_start", lambda args: time.perf_counter())
        self._define_builtin("stopwatch_elapsed", lambda args: time.perf_counter() - float(args[0]) if args else 0.0)

        # ── HTTP Kütüphanesi ──
        self._define_builtin("http_get", self._builtin_http_get)
        self._define_builtin("http_post", self._builtin_http_post)
        self._define_builtin("http_put", self._builtin_http_put)
        self._define_builtin("http_delete", self._builtin_http_delete)
        self._define_builtin("http_download", self._builtin_http_download)

        # ── JSON ──
        self._define_builtin("json_parse", self._builtin_json_parse)
        self._define_builtin("json_stringify", self._builtin_json_stringify)

        # ── Sistem Bilgisi ──
        self._define_builtin("env_get", lambda args: os.environ.get(str(args[0]), str(args[1]) if len(args) > 1 else "") if args else "")
        self._define_builtin("env_set", lambda args: os.environ.__setitem__(str(args[0]), str(args[1])) if len(args) >= 2 else None)
        self._define_builtin("platform", lambda args: sys.platform)
        self._define_builtin("pid", lambda args: os.getpid())

        # ── Native Köprüler (Bridges) ──
        self._setup_native_bridges()

    def _setup_native_bridges(self):
        """Native C++ kütüphanelerini yükler (Memory, Portswinger)"""
        try:
            from bridges.mrr_memory_bridge import MemoryReader
            self.memory_reader = MemoryReader()
            
            self._define_builtin("memory_attach", lambda args: self.memory_reader.attach(args[0]) if args else None)
            self._define_builtin("memory_process_list", lambda args: self.memory_reader.get_process_list())
        except Exception as e:
            # Sessizce devam et, hata sadece özellikleri kısıtlar
            self.memory_reader = None

        try:
            from bridges.mrr_portswinger_bridge import Portswinger
            self.portswinger = Portswinger()
            
            self._define_builtin("portswinger_http", lambda args: self.portswinger.http_request(
                str(args[0]), str(args[1]), 
                str(args[2]) if len(args) > 2 else "", 
                str(args[3]) if len(args) > 3 else ""
            ) if len(args) >= 2 else {})
            self._define_builtin("portswinger_socket_create", lambda args: self.portswinger.socket_create(
                int(args[0]) if len(args) > 0 else 2,
                int(args[1]) if len(args) > 1 else 1,
                int(args[2]) if len(args) > 2 else 0
            ))
            self._define_builtin("portswinger_socket_connect", lambda args: self.portswinger.socket_connect(
                int(args[0]), str(args[1]), int(args[2])
            ) if len(args) >= 3 else -1)
            self._define_builtin("portswinger_socket_send", lambda args: self.portswinger.socket_send(
                int(args[0]), str(args[1]).encode('utf-8')
            ) if len(args) >= 2 else -1)
            self._define_builtin("portswinger_socket_recv", lambda args: self.portswinger.socket_recv(
                int(args[0]), int(args[1])
            ).decode('utf-8', errors='replace') if len(args) >= 2 else "")
            self._define_builtin("portswinger_socket_close", lambda args: self.portswinger.socket_close(
                int(args[0])
            ) if args else None)
        except Exception as e:
            self.portswinger = None

    def _define_builtin(self, name: str, fn: Callable) -> None:
        func = MRRFunction(
            name=name, params=[], body=[], closure=self.global_env,
            is_builtin=True, builtin_fn=fn
        )
        self.global_env.define(name, func)

    # Yerleşik fonksiyon implementasyonları
    def _builtin_print(self, args: List[Any]) -> None:
        parts = []
        for a in args:
            parts.append(self._format_value(a))
        print(" ".join(parts), end="")

    def _builtin_println(self, args: List[Any]) -> None:
        parts = []
        for a in args:
            parts.append(self._format_value(a))
        print(" ".join(parts))

    def _builtin_input(self, args: List[Any]) -> MRRUntrustedString:
        prompt = str(args[0]) if args else ""
        return MRRUntrustedString(input(prompt))

    def _builtin_integer(self, args: List[Any]) -> int:
        if args and isinstance(args[0], str) and len(args) == 1:
            try:
                # integer("prompt") => ekrana yazdır ve girdi al
                return int(input(args[0]))
            except ValueError:
                return 0
        elif args:
            try:
                return int(args[0])
            except ValueError:
                return 0
        return 0

    def _builtin_alloc(self, args: List[Any]) -> MRRPointer:
        size = int(args[0]) if args else 0
        element_type = str(args[1]) if len(args) > 1 else "byte"
        return MRRPointer(buffer=bytearray(size), offset=0, element_type=element_type)

    def _builtin_free(self, args: List[Any]) -> None:
        if not args:
            return None
        ptr = args[0]
        if isinstance(ptr, MRRPointer):
            ptr.free()
        return None

    def _builtin_range(self, args: List[Any]) -> range:
        if len(args) == 1:
            return range(int(args[0]))
        elif len(args) == 2:
            return range(int(args[0]), int(args[1]))
        elif len(args) == 3:
            return range(int(args[0]), int(args[1]), int(args[2]))
        return range(0)

    def _builtin_sizeof(self, args: List[Any]) -> int:
        if not args:
            return 0
        v = args[0]
        if isinstance(v, int):
            return 8
        elif isinstance(v, float):
            return 8
        elif isinstance(v, str):
            return len(v.encode("utf-8"))
        elif isinstance(v, (bytes, bytearray)):
            return len(v)
        elif isinstance(v, list):
            return len(v) * 8
        return 0

    def _builtin_format(self, args: List[Any]) -> str:
        if not args:
            return ""
        template = str(args[0])
        for i, arg in enumerate(args[1:], 1):
            template = template.replace(f"{{{i - 1}}}", str(arg))
        return template

    def _builtin_map(self, args: List[Any]) -> list:
        if len(args) < 2:
            return []
        fn, collection = args[0], args[1]
        result = []
        for item in collection:
            if isinstance(fn, MRRFunction):
                result.append(self._call_function(fn, [item], self.global_env))
            elif callable(fn):
                result.append(fn(item))
        return result

    def _builtin_filter(self, args: List[Any]) -> list:
        if len(args) < 2:
            return []
        fn, collection = args[0], args[1]
        result = []
        for item in collection:
            if isinstance(fn, MRRFunction):
                val = self._call_function(fn, [item], self.global_env)
            elif callable(fn):
                val = fn(item)
            else:
                val = False
            if self._is_truthy(val):
                result.append(item)
        return result

    def _builtin_reduce(self, args: List[Any]) -> Any:
        if len(args) < 2:
            return None
        fn, collection = args[0], args[1]
        acc = args[2] if len(args) > 2 else collection[0]
        start = 0 if len(args) > 2 else 1
        for item in list(collection)[start:]:
            if isinstance(fn, MRRFunction):
                acc = self._call_function(fn, [acc, item], self.global_env)
            elif callable(fn):
                acc = fn(acc, item)
        return acc

    def _builtin_assert(self, args: List[Any]) -> None:
        if not args:
            raise MRRRuntimeError("assert() en az bir argüman gerektirir")
        condition = args[0]
        message = str(args[1]) if len(args) > 1 else "Doğrulama başarısız"
        if not self._is_truthy(condition):
            raise MRRRuntimeError(f"Assert hatası: {message}")

    def _builtin_type_name(self, args: List[Any]) -> str:
        if not args:
            return "void"
        v = args[0]
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, int):
            return "i64"
        if isinstance(v, float):
            return "f64"
        if isinstance(v, str):
            return "str"
        if isinstance(v, list):
            return "list"
        if isinstance(v, dict):
            return "dict"
        if isinstance(v, MRRStruct):
            return v.name
        if isinstance(v, MRRInstance):
            return v.class_ref.name
        if isinstance(v, MRRFunction):
            return "fn"
        return type(v).__name__

    def _builtin_readfile(self, args: List[Any]) -> MRRUntrustedString:
        if not args:
            raise MRRRuntimeError("readfile() dosya yolu gerektirir")
        try:
            with open(str(args[0]), "r", encoding="utf-8") as f:
                return MRRUntrustedString(f.read())
        except FileNotFoundError:
            raise MRRRuntimeError(f"Dosya bulunamadı: {args[0]}")
        except Exception as e:
            raise MRRRuntimeError(f"Dosya okuma hatası: {e}")

    def _builtin_system(self, args: List[Any]) -> int:
        if not args:
            return 0
        if isinstance(args[0], MRRUntrustedString):
            raise MRRRuntimeError("GÜVENLİK İHLALİ: system() fonksiyonuna Untrusted veri gönderildi. Lütfen önce sanitize() kullanın.")
        return os.system(str(args[0]))

    def _builtin_writefile(self, args: List[Any]) -> bool:
        if len(args) < 2:
            raise MRRRuntimeError("writefile(dosya, içerik) gerektirir")
        try:
            with open(str(args[0]), "w", encoding="utf-8") as f:
                f.write(str(args[1]))
            return True
        except Exception as e:
            raise MRRRuntimeError(f"Dosya yazma hatası: {e}")

    # ─────────────────────────────────────────────────────
    # Gelişmiş Dosya I/O İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_file_read_lines(self, args: List[Any]) -> list:
        if not args:
            raise MRRRuntimeError("file_read_lines(dosya) gerektirir")
        try:
            with open(str(args[0]), "r", encoding="utf-8") as f:
                return [line.rstrip('\n') for line in f.readlines()]
        except Exception as e:
            raise MRRRuntimeError(f"Dosya okuma hatası: {e}")

    def _builtin_file_append(self, args: List[Any]) -> bool:
        if len(args) < 2:
            raise MRRRuntimeError("file_append(dosya, içerik) gerektirir")
        try:
            with open(str(args[0]), "a", encoding="utf-8") as f:
                f.write(str(args[1]))
            return True
        except Exception as e:
            raise MRRRuntimeError(f"Dosya ekleme hatası: {e}")

    def _builtin_file_delete(self, args: List[Any]) -> bool:
        if not args:
            raise MRRRuntimeError("file_delete(dosya) gerektirir")
        try:
            os.remove(str(args[0]))
            return True
        except Exception as e:
            raise MRRRuntimeError(f"Dosya silme hatası: {e}")

    def _builtin_file_copy(self, args: List[Any]) -> bool:
        if len(args) < 2:
            raise MRRRuntimeError("file_copy(kaynak, hedef) gerektirir")
        try:
            import shutil
            shutil.copy2(str(args[0]), str(args[1]))
            return True
        except Exception as e:
            raise MRRRuntimeError(f"Dosya kopyalama hatası: {e}")

    def _builtin_dir_list(self, args: List[Any]) -> list:
        if not args:
            raise MRRRuntimeError("dir_list(dizin) gerektirir")
        try:
            return os.listdir(str(args[0]))
        except Exception as e:
            raise MRRRuntimeError(f"Dizin listeleme hatası: {e}")

    def _builtin_dir_create(self, args: List[Any]) -> bool:
        if not args:
            raise MRRRuntimeError("dir_create(dizin) gerektirir")
        try:
            os.makedirs(str(args[0]), exist_ok=True)
            return True
        except Exception as e:
            raise MRRRuntimeError(f"Dizin oluşturma hatası: {e}")

    # ─────────────────────────────────────────────────────
    # Regex İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_regex_match(self, args: List[Any]) -> bool:
        if len(args) < 2:
            return False
        return bool(re.search(str(args[0]), str(args[1])))

    def _builtin_regex_find_all(self, args: List[Any]) -> list:
        if len(args) < 2:
            return []
        return re.findall(str(args[0]), str(args[1]))

    def _builtin_regex_replace(self, args: List[Any]) -> str:
        if len(args) < 3:
            return str(args[1]) if len(args) >= 2 else ""
        return re.sub(str(args[0]), str(args[1]), str(args[2]))

    # ─────────────────────────────────────────────────────
    # Encoding İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_encode_base64(self, args: List[Any]) -> str:
        if not args:
            return ""
        import base64
        data = str(args[0]).encode('utf-8')
        return base64.b64encode(data).decode('utf-8')

    def _builtin_decode_base64(self, args: List[Any]) -> str:
        if not args:
            return ""
        import base64
        try:
            return base64.b64decode(str(args[0])).decode('utf-8')
        except Exception:
            raise MRRRuntimeError("Geçersiz Base64 verisi")

    def _builtin_encode_url(self, args: List[Any]) -> str:
        if not args:
            return ""
        import urllib.parse
        return urllib.parse.quote(str(args[0]), safe='')

    def _builtin_decode_url(self, args: List[Any]) -> str:
        if not args:
            return ""
        import urllib.parse
        return urllib.parse.unquote(str(args[0]))

    # ─────────────────────────────────────────────────────
    # Gelişmiş Koleksiyon İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_find(self, args: List[Any]) -> Any:
        if len(args) < 2:
            return None
        fn, collection = args[0], args[1]
        for item in collection:
            if isinstance(fn, MRRFunction):
                if self._is_truthy(self._call_function(fn, [item], self.global_env)):
                    return item
        return None

    def _builtin_find_index(self, args: List[Any]) -> int:
        if len(args) < 2:
            return -1
        fn, collection = args[0], args[1]
        for i, item in enumerate(collection):
            if isinstance(fn, MRRFunction):
                if self._is_truthy(self._call_function(fn, [item], self.global_env)):
                    return i
        return -1

    def _builtin_every(self, args: List[Any]) -> bool:
        if len(args) < 2:
            return True
        fn, collection = args[0], args[1]
        for item in collection:
            if isinstance(fn, MRRFunction):
                if not self._is_truthy(self._call_function(fn, [item], self.global_env)):
                    return False
        return True

    def _builtin_some(self, args: List[Any]) -> bool:
        if len(args) < 2:
            return False
        fn, collection = args[0], args[1]
        for item in collection:
            if isinstance(fn, MRRFunction):
                if self._is_truthy(self._call_function(fn, [item], self.global_env)):
                    return True
        return False

    def _builtin_chunk(self, args: List[Any]) -> list:
        if len(args) < 2:
            return [list(args[0])] if args else []
        lst = list(args[0])
        size = int(args[1])
        return [lst[i:i+size] for i in range(0, len(lst), size)]

    def _builtin_group_by(self, args: List[Any]) -> dict:
        if len(args) < 2:
            return {}
        fn, collection = args[0], args[1]
        result = {}
        for item in collection:
            if isinstance(fn, MRRFunction):
                key = self._call_function(fn, [item], self.global_env)
            else:
                key = str(fn)
            if key not in result:
                result[key] = []
            result[key].append(item)
        return result

    def _builtin_count_if(self, args: List[Any]) -> int:
        if len(args) < 2:
            return 0
        fn, collection = args[0], args[1]
        count = 0
        for item in collection:
            if isinstance(fn, MRRFunction):
                if self._is_truthy(self._call_function(fn, [item], self.global_env)):
                    count += 1
        return count

    def _builtin_zip_with(self, args: List[Any]) -> list:
        if len(args) < 3:
            return []
        fn, list_a, list_b = args[0], args[1], args[2]
        result = []
        for a, b in zip(list_a, list_b):
            if isinstance(fn, MRRFunction):
                result.append(self._call_function(fn, [a, b], self.global_env))
        return result

    def _flatten_list(self, lst: list) -> list:
        result = []
        for item in lst:
            if isinstance(item, list):
                result.extend(self._flatten_list(item))
            else:
                result.append(item)
        return result

    # ─────────────────────────────────────────────────────
    # Tarih ve Saat İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_now_str(self, args: List[Any]) -> str:
        fmt = str(args[0]) if args else "%Y-%m-%d %H:%M:%S"
        return time.strftime(fmt)

    def _builtin_date_format(self, args: List[Any]) -> str:
        if len(args) < 2:
            return time.strftime("%Y-%m-%d %H:%M:%S")
        timestamp = float(args[0])
        fmt = str(args[1])
        return time.strftime(fmt, time.localtime(timestamp))

    def _builtin_date_parse(self, args: List[Any]) -> float:
        if len(args) < 2:
            raise MRRRuntimeError("date_parse(string, format) gerektirir")
        import calendar
        try:
            t = time.strptime(str(args[0]), str(args[1]))
            return float(calendar.timegm(t))
        except ValueError as e:
            raise MRRRuntimeError(f"Tarih ayrıştırma hatası: {e}")

    def _builtin_date_component(self, component: str):
        def getter(args: List[Any]) -> int:
            ts = float(args[0]) if args else time.time()
            t = time.localtime(ts)
            return getattr(t, component)
        return getter

    def _is_leap_year(self, year: int) -> bool:
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    # ─────────────────────────────────────────────────────
    # HTTP Kütüphanesi İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _make_http_request(self, method: str, url: str, body: Any = None,
                            headers: Any = None) -> dict:
        import urllib.request
        import urllib.error
        import urllib.parse

        hdrs = {
            'User-Agent': 'MRR-HTTP/1.0',
            'Accept': '*/*',
        }
        if isinstance(headers, dict):
            hdrs.update(headers)

        data = None
        if body is not None:
            if isinstance(body, dict):
                import json as json_mod
                data = json_mod.dumps(body).encode('utf-8')
                hdrs.setdefault('Content-Type', 'application/json')
            elif isinstance(body, str):
                data = body.encode('utf-8')
            elif isinstance(body, bytes):
                data = body

        try:
            req = urllib.request.Request(url, data=data, headers=hdrs, method=method)
            with urllib.request.urlopen(req, timeout=30) as resp:
                resp_body = resp.read().decode('utf-8', errors='replace')
                return {
                    'status': resp.status,
                    'body': resp_body,
                    'headers': dict(resp.headers),
                    'url': resp.url,
                    'error': None,
                }
        except urllib.error.HTTPError as e:
            return {
                'status': e.code,
                'body': e.read().decode('utf-8', errors='replace'),
                'headers': dict(e.headers) if e.headers else {},
                'url': url,
                'error': str(e),
            }
        except Exception as e:
            return {
                'status': 0,
                'body': '',
                'headers': {},
                'url': url,
                'error': str(e),
            }

    def _builtin_http_get(self, args: List[Any]) -> dict:
        if not args:
            raise MRRRuntimeError("http_get(url, headers?) gerektirir")
        url = str(args[0])
        headers = args[1] if len(args) > 1 and isinstance(args[1], dict) else None
        return self._make_http_request('GET', url, headers=headers)

    def _builtin_http_post(self, args: List[Any]) -> dict:
        if not args:
            raise MRRRuntimeError("http_post(url, body, headers?) gerektirir")
        url = str(args[0])
        body = args[1] if len(args) > 1 else None
        headers = args[2] if len(args) > 2 and isinstance(args[2], dict) else None
        return self._make_http_request('POST', url, body=body, headers=headers)

    def _builtin_http_put(self, args: List[Any]) -> dict:
        if not args:
            raise MRRRuntimeError("http_put(url, body, headers?) gerektirir")
        url = str(args[0])
        body = args[1] if len(args) > 1 else None
        headers = args[2] if len(args) > 2 and isinstance(args[2], dict) else None
        return self._make_http_request('PUT', url, body=body, headers=headers)

    def _builtin_http_delete(self, args: List[Any]) -> dict:
        if not args:
            raise MRRRuntimeError("http_delete(url, headers?) gerektirir")
        url = str(args[0])
        headers = args[1] if len(args) > 1 and isinstance(args[1], dict) else None
        return self._make_http_request('DELETE', url, headers=headers)

    def _builtin_http_download(self, args: List[Any]) -> bool:
        if len(args) < 2:
            raise MRRRuntimeError("http_download(url, dosya_yolu) gerektirir")
        import urllib.request
        try:
            urllib.request.urlretrieve(str(args[0]), str(args[1]))
            return True
        except Exception as e:
            raise MRRRuntimeError(f"İndirme hatası: {e}")

    # ─────────────────────────────────────────────────────
    # JSON İmplementasyonları
    # ─────────────────────────────────────────────────────

    def _builtin_json_parse(self, args: List[Any]) -> Any:
        if not args:
            raise MRRRuntimeError("json_parse(string) gerektirir")
        import json as json_mod
        try:
            return json_mod.loads(str(args[0]))
        except json_mod.JSONDecodeError as e:
            raise MRRRuntimeError(f"JSON ayrıştırma hatası: {e}")

    def _builtin_json_stringify(self, args: List[Any]) -> str:
        if not args:
            return "null"
        import json as json_mod
        indent = int(args[1]) if len(args) > 1 else None
        try:
            return json_mod.dumps(args[0], indent=indent, ensure_ascii=False, default=str)
        except Exception as e:
            raise MRRRuntimeError(f"JSON serileştirme hatası: {e}")

    def _format_value(self, value: Any) -> str:
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, MRRStruct):
            return repr(value)
        if isinstance(value, MRRInstance):
            return repr(value)
        if isinstance(value, MRRFunction):
            return f"<fn {value.name}>"
        if isinstance(value, bytes):
            return value.hex()
        if isinstance(value, dict):
            pairs = ", ".join(f"{self._format_value(k)}: {self._format_value(v)}" for k, v in value.items())
            return "{" + pairs + "}"
        if isinstance(value, list):
            items = ", ".join(self._format_value(v) for v in value)
            return f"[{items}]"
        return str(value)

    # ─────────────────────────────────────────────────────
    # Ana Çalıştırma
    # ─────────────────────────────────────────────────────

    def execute(self, program: Program) -> Any:
        """Programı çalıştır."""
        result = None
        for node in program.body:
            result = self._exec(node, self.global_env)
        return result

    def _exec(self, node: ASTNode, env: Environment) -> Any:
        """Bir AST düğümünü çalıştır."""
        if node is None:
            return None

        method_name = f"_exec_{type(node).__name__}"
        method = getattr(self, method_name, None)
        if method:
            return method(node, env)

        raise MRRRuntimeError(
            f"Bilinmeyen AST düğümü: {type(node).__name__}",
            getattr(node, 'location', None)
        )

    # ─────────────────────────────────────────────────────
    # Bildirim Çalıştırıcıları
    # ─────────────────────────────────────────────────────

    def _exec_ModuleDecl(self, node: ModuleDecl, env: Environment) -> None:
        pass  # Modül adı kaydet, ileride namespace olarak kullanılacak

    def _exec_AddCodeDecl(self, node: AddCodeDecl, env: Environment) -> None:
        """FFI kütüphane yükleme: add.code "library" """
        if self.ffi_bridge:
            module = self.ffi_bridge.load_library(node.library, node.alias, node.imports)
            if module is not None:
                name = node.alias or node.library
                env.define(name, module, mutable=False)
                self._loaded_libs[node.library] = module
        else:
            raise MRRRuntimeError(
                f"FFI bridge yüklenmedi. '{node.library}' aktarılamıyor.",
                node.location
            )

    def _exec_UseDecl(self, node: UseDecl, env: Environment) -> None:
        pass  # Phase 3: Modül sistemi

    def _exec_FunctionDecl(self, node: FunctionDecl, env: Environment) -> None:
        """Fonksiyon tanımlama — closure yakalar."""
        func = MRRFunction(
            name=node.name,
            params=node.params,
            body=node.body,
            closure=env,
            return_type=node.return_type,
            is_async=getattr(node, 'is_async', False)
        )
        env.define(node.name, func, mutable=False)

    def _exec_VarDecl(self, node: VarDecl, env: Environment) -> None:
        """Değişken tanımlama."""
        value = None
        if node.initializer:
            value = self._exec(node.initializer, env)
            
        if getattr(node, 'is_temporal', False):
            value = MRRTemporalVar(value)
            
        env.define(node.name, value, mutable=node.is_mutable)

    def _exec_StructDecl(self, node: StructDecl, env: Environment) -> None:
        """Struct tanımlama — constructor fonksiyonu olarak kaydet."""
        def struct_constructor(args):
            s = MRRStruct(name=node.name)
            for i, fld in enumerate(node.fields):
                if i < len(args):
                    s.fields[fld.name] = args[i]
                else:
                    s.fields[fld.name] = None
            return s

        ctor = MRRFunction(
            name=node.name, params=node.fields, body=[],
            closure=env, is_builtin=True, builtin_fn=struct_constructor
        )
        env.define(node.name, ctor, mutable=False)

    def _exec_ClassDecl(self, node: ClassDecl, env: Environment) -> None:
        """Sınıf tanımlama."""
        cls = MRRClass(name=node.name, bases=node.base_classes)
        class_env = env.child(f"class_{node.name}")

        for stmt in node.body:
            if isinstance(stmt, FunctionDecl):
                fn = MRRFunction(
                    name=stmt.name, params=stmt.params,
                    body=stmt.body, closure=class_env
                )
                cls.methods[stmt.name] = fn
            else:
                self._exec(stmt, class_env)

        # Sınıf constructor
        def class_constructor(args):
            inst = MRRInstance(class_ref=cls, fields={})
            if "__init__" in cls.methods or "new" in cls.methods:
                init_name = "__init__" if "__init__" in cls.methods else "new"
                init_fn = cls.methods[init_name]
                self._call_function(init_fn, [inst] + args, env)
            return inst

        ctor = MRRFunction(
            name=node.name, params=[], body=[],
            closure=env, is_builtin=True, builtin_fn=class_constructor
        )
        env.define(node.name, ctor, mutable=False)

    def _exec_TraitDecl(self, node: TraitDecl, env: Environment) -> None:
        pass  # Trait'ler derleme zamanı konsepti — interpreter'da no-op

    def _exec_ImplDecl(self, node: ImplDecl, env: Environment) -> None:
        """Implementasyon bloğu — metotları tipe ekle."""
        for method in node.methods:
            method_name = f"{node.type_name}__{method.name}"
            fn = MRRFunction(
                name=method_name, params=method.params,
                body=method.body, closure=env
            )
            env.define(method_name, fn, mutable=False)

    def _exec_ExploitDecl(self, node: ExploitDecl, env: Environment) -> None:
        exploit_env = env.child(f"exploit_{node.name}")
        for stmt in node.body:
            self._exec(stmt, exploit_env)

    def _exec_DriverDecl(self, node: DriverDecl, env: Environment) -> None:
        print(f"[MRR] ⚠ Kernel driver '{node.name}' interpreter modunda çalıştırılamaz.")
        print(f"[MRR]   Derleyici modu gerekli: mrr compile --driver {node.name}.mrr")

    def _exec_HookDecl(self, node: HookDecl, env: Environment) -> None:
        print(f"[MRR] ⚠ Hook '{node.target}' interpreter modunda simüle ediliyor.")

    # ─────────────────────────────────────────────────────
    # Kontrol Akışı Çalıştırıcıları
    # ─────────────────────────────────────────────────────

    def _exec_IfStmt(self, node: IfStmt, env: Environment) -> Any:
        if self._is_truthy(self._exec(node.condition, env)):
            return self._exec_block(node.then_body, env)

        for cond, body in node.elif_clauses:
            if self._is_truthy(self._exec(cond, env)):
                return self._exec_block(body, env)

        if node.else_body:
            return self._exec_block(node.else_body, env)

        return None

    def _exec_ForStmt(self, node: ForStmt, env: Environment) -> None:
        iterable = self._exec(node.iterable, env)
        for item in iterable:
            loop_env = env.child("for")
            loop_env.define(node.variable, item, mutable=True)
            try:
                self._exec_block(node.body, loop_env)
            except MRRBreak:
                break
            except MRRContinue:
                continue

    def _exec_WhileStmt(self, node: WhileStmt, env: Environment) -> None:
        while self._is_truthy(self._exec(node.condition, env)):
            loop_env = env.child("while")
            try:
                self._exec_block(node.body, loop_env)
            except MRRBreak:
                break
            except MRRContinue:
                continue

    def _exec_LoopStmt(self, node: LoopStmt, env: Environment) -> None:
        while True:
            loop_env = env.child("loop")
            try:
                self._exec_block(node.body, loop_env)
            except MRRBreak:
                break
            except MRRContinue:
                continue

    def _exec_MatchStmt(self, node: MatchStmt, env: Environment) -> Any:
        value = self._exec(node.value, env)
        for pattern, body in node.arms:
            pat_val = self._exec(pattern, env)
            if pat_val == "_" or pat_val == value:
                return self._exec(body, env)
        return None

    def _exec_ReturnStmt(self, node: ReturnStmt, env: Environment) -> None:
        value = self._exec(node.value, env) if node.value else None
        raise MRRReturn(value)

    def _exec_BreakStmt(self, node: BreakStmt, env: Environment) -> None:
        raise MRRBreak()

    def _exec_ContinueStmt(self, node: ContinueStmt, env: Environment) -> None:
        raise MRRContinue()

    def _exec_PassStmt(self, node: PassStmt, env: Environment) -> None:
        pass

    def _exec_UnsafeBlock(self, node: UnsafeBlock, env: Environment) -> Any:
        return self._exec_block(node.body, env)

    def _exec_KernelBlock(self, node: KernelBlock, env: Environment) -> Any:
        print("[MRR] ⚠ Ring-0 kernel bloğu interpreter modunda simüle ediliyor.")
        return self._exec_block(node.body, env)

    def _exec_PrintStmt(self, node: PrintStmt, env: Environment) -> None:
        if node.value:
            val = self._exec(node.value, env)
            text = self._format_value(val)
            text = self._interpolate_string(text, env)
            if node.newline:
                print(text)
            else:
                print(text, end="")
        elif node.newline:
            print()

    # ─────────────────────────────────────────────────────
    # İfade Çalıştırıcıları
    # ─────────────────────────────────────────────────────

    def _exec_ExpressionStmt(self, node: ExpressionStmt, env: Environment) -> Any:
        return self._exec(node.expression, env)

    def _exec_AsmExpr(self, node: AsmExpr, env: Environment) -> Any:
        # Inline assembly is simulated in interpreter mode.
        # Returning 0 as a placeholder for register/memory results.
        return 0

    def _exec_ShellcodeExpr(self, node: ShellcodeExpr, env: Environment) -> Any:
        return MRRShellcode(arch=node.arch, code=node.code)

    def _exec_LiteralExpr(self, node: LiteralExpr, env: Environment) -> Any:
        return node.value

    def _exec_IdentifierExpr(self, node: IdentifierExpr, env: Environment) -> Any:
        return env.get(node.name)

    def _exec_BinaryExpr(self, node: BinaryExpr, env: Environment) -> Any:
        left = self._exec(node.left, env)
        right = self._exec(node.right, env)

        op = node.operator
        try:
            match op:
                case "+":  return left + right
                case "-":  return left - right
                case "*":  return left * right
                case "/":
                    if right == 0:
                        raise MRRRuntimeError("Sıfıra bölme hatası", node.location)
                    if isinstance(left, int) and isinstance(right, int):
                        return left // right
                    return left / right
                case "%":  return left % right
                case "**": return left ** right
                case "&":  return left & right
                case "|":  return left | right
                case "^":  return left ^ right
                case "<<": return left << right
                case ">>": return left >> right
                case "==": return left == right
                case "!=": return left != right
                case "<":  return left < right
                case ">":  return left > right
                case "<=": return left <= right
                case ">=": return left >= right
                case "and" | "&&": return left and right
                case "or"  | "||": return left or right
                case "is": return left is right
                case "in": return left in right
                case "??":
                    return left if left is not None else right
                case _:
                    raise MRRRuntimeError(f"Bilinmeyen operatör: {op}", node.location)
        except TypeError as e:
            raise MRRRuntimeError(
                f"Tip uyumsuzluğu: {type(left).__name__} {op} {type(right).__name__}",
                node.location
            )

    def _exec_UnaryExpr(self, node: UnaryExpr, env: Environment) -> Any:
        val = self._exec(node.operand, env)
        match node.operator:
            case "-":            return -val
            case "!" | "not":    return not val
            case "~":            return ~val
            case _:
                raise MRRRuntimeError(f"Bilinmeyen tekli operatör: {node.operator}")

    def _exec_CallExpr(self, node: CallExpr, env: Environment) -> Any:
        callee = self._exec(node.callee, env)
        args = [self._exec(arg, env) for arg in node.arguments]

        if isinstance(callee, MRRFunction):
            if callee.is_async:
                return MRRFuture(self, callee, args, env)
            return self._call_function(callee, args, env)

        # Python callable (FFI'den gelen)
        if callable(callee):
            try:
                return callee(*args)
            except Exception as e:
                raise MRRRuntimeError(f"FFI çağrı hatası: {e}", node.location)

        raise MRRRuntimeError(
            f"'{self._format_value(callee)}' çağrılabilir değil",
            node.location
        )

    def _call_function(self, func: MRRFunction, args: List[Any],
                       caller_env: Environment) -> Any:
        if func.is_builtin and func.builtin_fn:
            return func.builtin_fn(args)

        fn_env = func.closure.child(f"fn_{func.name}")

        # Parametreleri bağla
        for i, param in enumerate(func.params):
            if i < len(args):
                fn_env.define(param.name, args[i], mutable=param.is_mut)
            elif param.default_value:
                default_val = self._exec(param.default_value, caller_env)
                fn_env.define(param.name, default_val, mutable=param.is_mut)
            else:
                fn_env.define(param.name, None, mutable=param.is_mut)

        try:
            self._exec_block(func.body, fn_env)
        except MRRReturn as ret:
            return ret.value

        return None

    def _exec_MemberAccessExpr(self, node: MemberAccessExpr,
                                env: Environment) -> Any:
        
        # Temporal .rollback() desteği
        if isinstance(node.object, IdentifierExpr):
            try:
                raw_obj = env.get_raw(node.object.name)
                if isinstance(raw_obj, MRRTemporalVar) and node.member == "rollback":
                    def rollback_fn(args):
                        steps = int(args[0]) if args else 1
                        raw_obj.rollback(steps)
                        return raw_obj.value
                    return MRRFunction(name="rollback", params=[], body=[], closure=env, is_builtin=True, builtin_fn=rollback_fn)
            except MRRRuntimeError:
                pass
                
        obj = self._exec(node.object, env)

        # MRR struct erişimi
        if isinstance(obj, MRRStruct):
            if node.member in obj.fields:
                return obj.fields[node.member]
            raise MRRRuntimeError(
                f"'{obj.name}' üzerinde '{node.member}' alanı bulunamadı",
                node.location
            )

        # MRR instance erişimi
        if isinstance(obj, MRRInstance):
            if node.member in obj.fields:
                return obj.fields[node.member]
            if node.member in obj.class_ref.methods:
                method = obj.class_ref.methods[node.member]
                # Metoda self'i bind et
                def bound_method(*args):
                    return self._call_function(method, [obj] + list(args), env)
                return bound_method
            raise MRRRuntimeError(
                f"'{obj.class_ref.name}' üzerinde '{node.member}' bulunamadı",
                node.location
            )

        # Python nesnesi (FFI)
        try:
            return getattr(obj, node.member)
        except AttributeError:
            raise MRRRuntimeError(
                f"'{type(obj).__name__}' üzerinde '{node.member}' bulunamadı",
                node.location
            )

    def _exec_IndexExpr(self, node: IndexExpr, env: Environment) -> Any:
        obj = self._exec(node.object, env)
        index = self._exec(node.index, env)
        try:
            return obj[index]
        except (IndexError, KeyError, TypeError) as e:
            raise MRRRuntimeError(f"İndeks hatası: {e}", node.location)

    def _exec_CastExpr(self, node: CastExpr, env: Environment) -> Any:
        val = self._exec(node.operand, env)
        type_map = {
            "i8": lambda v: int(v) & 0x7F,
            "i16": lambda v: int(v) & 0x7FFF,
            "i32": lambda v: int(v) & 0x7FFFFFFF,
            "i64": int,
            "u8": lambda v: int(v) & 0xFF,
            "u16": lambda v: int(v) & 0xFFFF,
            "u32": lambda v: int(v) & 0xFFFFFFFF,
            "u64": lambda v: int(v) & 0xFFFFFFFFFFFFFFFF,
            "f32": float,
            "f64": float,
            "str": str,
            "bool": bool,
            "byte": lambda v: int(v) & 0xFF,
        }
        if node.target_type in type_map:
            return type_map[node.target_type](val)
        if node.target_type.startswith("ptr"):
            return self._cast_to_pointer(val, node.target_type)
        return val

    def _cast_to_pointer(self, value: Any, target_type: str) -> MRRPointer:
        if isinstance(value, MRRPointer):
            return value.as_type(target_type)
        if isinstance(value, int):
            return MRRPointer(buffer=bytearray(), offset=0, element_type=target_type, address=value)
        if isinstance(value, (bytes, bytearray)):
            return MRRPointer(buffer=bytearray(value), offset=0, element_type=target_type)
        return MRRPointer(buffer=bytearray(str(value).encode("utf-8")), offset=0, element_type=target_type)

    def _exec_RangeExpr(self, node: RangeExpr, env: Environment) -> range:
        start = self._exec(node.start, env) if node.start else 0
        end = self._exec(node.end, env)
        if node.inclusive:
            end += 1
        return range(int(start), int(end))

    def _exec_ListExpr(self, node: ListExpr, env: Environment) -> list:
        return [self._exec(el, env) for el in node.elements]

    def _exec_AssignExpr(self, node: AssignExpr, env: Environment) -> Any:
        value = self._exec(node.value, env)

        if isinstance(node.target, IdentifierExpr):
            if node.operator == "=":
                env.set(node.target.name, value)
            else:
                current = env.get(node.target.name)
                # Operatörden = işaretini kaldır: += → +, <<= → <<, **= → **
                op = node.operator[:-1]
                value = self._apply_op(current, op, value)
                env.set(node.target.name, value)
        elif isinstance(node.target, MemberAccessExpr):
            obj = self._exec(node.target.object, env)
            if node.operator != "=":
                current = obj.fields.get(node.target.member) if isinstance(obj, (MRRStruct, MRRInstance)) else getattr(obj, node.target.member)
                op = node.operator[:-1]
                value = self._apply_op(current, op, value)
            if isinstance(obj, (MRRStruct, MRRInstance)):
                obj.fields[node.target.member] = value
            else:
                setattr(obj, node.target.member, value)
        elif isinstance(node.target, IndexExpr):
            obj = self._exec(node.target.object, env)
            idx = self._exec(node.target.index, env)
            if node.operator != "=":
                current = obj[idx]
                op = node.operator[:-1]
                value = self._apply_op(current, op, value)
            obj[idx] = value

        return value

    # ─────────────────────────────────────────────────────
    # Yeni İfade Çalıştırıcıları
    # ─────────────────────────────────────────────────────

    def _exec_DictExpr(self, node: DictExpr, env: Environment) -> dict:
        result = {}
        for key_node, val_node in node.pairs:
            key = self._exec(key_node, env)
            val = self._exec(val_node, env)
            result[key] = val
        return result

    def _exec_LambdaExpr(self, node: LambdaExpr, env: Environment) -> MRRFunction:
        from interpreter.mrr_parser import Parameter
        return MRRFunction(
            name="<lambda>",
            params=node.params,
            body=[node.body],
            closure=env,
            return_type=None
        )

    def _exec_TernaryExpr(self, node: TernaryExpr, env: Environment) -> Any:
        if self._is_truthy(self._exec(node.condition, env)):
            return self._exec(node.true_value, env)
        return self._exec(node.false_value, env)

    def _exec_TupleExpr(self, node: TupleExpr, env: Environment) -> tuple:
        return tuple(self._exec(el, env) for el in node.elements)

    def _exec_AwaitExpr(self, node: AwaitExpr, env: Environment) -> Any:
        future = self._exec(node.expression, env)
        if isinstance(future, MRRFuture):
            return future.result()
        if callable(future):
            return future()
        return future

    def _exec_PipeExpr(self, node: PipeExpr, env: Environment) -> Any:
        value = self._exec(node.value, env)
        func = self._exec(node.function, env)
        if isinstance(func, MRRFunction):
            return self._call_function(func, [value], env)
        elif callable(func):
            return func(value)
        raise MRRRuntimeError("Pipe operatörünün sağ tarafı bir fonksiyon olmalı", node.location)

    # ─────────────────────────────────────────────────────
    # Yeni Deyim Çalıştırıcıları
    # ─────────────────────────────────────────────────────

    def _exec_TryCatchStmt(self, node: TryCatchStmt, env: Environment) -> Any:
        try:
            return self._exec_block(node.try_body, env)
        except MRRRuntimeError as e:
            if node.catch_body:
                catch_env = env.child("catch")
                if node.catch_var:
                    catch_env.define(node.catch_var, str(e), mutable=False)
                return self._exec_block(node.catch_body, catch_env)
        except MRRReturn:
            raise
        except Exception as e:
            if node.catch_body:
                catch_env = env.child("catch")
                if node.catch_var:
                    catch_env.define(node.catch_var, str(e), mutable=False)
                return self._exec_block(node.catch_body, catch_env)
        finally:
            if node.finally_body:
                self._exec_block(node.finally_body, env)

    def _exec_ThrowStmt(self, node: ThrowStmt, env: Environment) -> None:
        value = self._exec(node.value, env) if node.value else "Bilinmeyen hata"
        raise MRRRuntimeError(str(value), node.location)

    def _exec_EnumDecl(self, node: EnumDecl, env: Environment) -> None:
        """Enum tanımlama — her variant'ı sabit olarak kaydet."""
        enum_dict = {}
        for vname, vexpr in node.variants:
            val = self._exec(vexpr, env)
            enum_dict[vname] = val
            # Her variant'ı EnumAdı::VariantAdı olarak da erişilebilir yap
            env.define(f"{node.name}__{vname}", val, mutable=False)

        # Enum'ı bir struct-benzeri nesne olarak kaydet
        enum_obj = MRRStruct(name=node.name, fields=enum_dict)
        env.define(node.name, enum_obj, mutable=False)

    def _exec_DeleteStmt(self, node: DeleteStmt, env: Environment) -> None:
        if isinstance(node.target, IdentifierExpr):
            if env.has(node.target.name):
                env._vars.pop(node.target.name, None)
                env._mutables.discard(node.target.name)
            else:
                raise MRRRuntimeError(f"Silinecek değişken bulunamadı: '{node.target.name}'")
        elif isinstance(node.target, IndexExpr):
            obj = self._exec(node.target.object, env)
            idx = self._exec(node.target.index, env)
            if isinstance(obj, list):
                del obj[int(idx)]
            elif isinstance(obj, dict):
                del obj[idx]
            else:
                raise MRRRuntimeError("delete yalnızca liste ve sözlük elemanları için kullanılabilir")
        else:
            raise MRRRuntimeError("delete hedefi geçersiz", node.location)

    def _exec_DoWhileStmt(self, node: DoWhileStmt, env: Environment) -> None:
        while True:
            loop_env = env.child("do_while")
            try:
                self._exec_block(node.body, loop_env)
            except MRRBreak:
                break
            except MRRContinue:
                pass
            if not self._is_truthy(self._exec(node.condition, env)):
                break

    def _exec_DeferStmt(self, node: DeferStmt, env: Environment) -> None:
        def deferred():
            try:
                self._exec_block(node.body, env)
            except Exception:
                pass
        env.register_defer(deferred)

    # ─────────────────────────────────────────────────────
    # Yardımcı Metotlar
    # ─────────────────────────────────────────────────────

    def _exec_block(self, stmts: List[ASTNode], env: Environment) -> Any:
        result = None
        block_env = env.child("block")
        try:
            for stmt in stmts:
                result = self._exec(stmt, block_env)
            return result
        finally:
            block_env.run_deferred()

    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return len(value) > 0
        if isinstance(value, list):
            return len(value) > 0
        return True

    def _apply_op(self, left: Any, op: str, right: Any) -> Any:
        match op:
            case "+":  return left + right
            case "-":  return left - right
            case "*":  return left * right
            case "/":  return left / right if right != 0 else 0
            case "%":  return left % right
            case "**": return left ** right
            case "&":  return left & right
            case "|":  return left | right
            case "^":  return left ^ right
            case "<<": return left << right
            case ">>": return left >> right
            case _:    return right

    def _interpolate_string(self, text: str, env: Environment) -> str:
        """#{expr} string interpolation."""
        def replace_match(m):
            expr_str = m.group(1)
            # Basit değişken ismi
            try:
                return self._format_value(env.get(expr_str))
            except MRRRuntimeError:
                return f"#{{{expr_str}}}"

        return re.sub(r'#\{([^}]+)\}', replace_match, text)
