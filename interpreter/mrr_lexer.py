"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Lexer — Sözcüksel Çözümleyici (Lexical Analyzer) v1.0.1   ║
║                                                                  ║
║  MRR dilinin kaynak kodunu Token akışına dönüştürür.            ║
║  Python/C# melezi sözdizimini destekler:                        ║
║    - Fonction.create "name" ():  → Fonksiyon tanımlama          ║
║    - add.code "kütüphane"        → FFI kütüphane aktarımı       ║
║    - Girinti tabanlı bloklar (Python-style indentation)         ║
║    - Siber güvenlik anahtar kelimeleri (kernel, ring0, exploit) ║
║                                                                  ║
║  v1.0.1 Resilient: Case-insensitive komut tanıma, gelişmiş     ║
║  hata kurtarma, BOM desteği, kırılganlık giderildi.            ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional


# ═══════════════════════════════════════════════════════════
# ─── TOKEN TİPLERİ ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class TokenType(Enum):
    """MRR dilinin tüm token tipleri."""

    # ── Son / Hata ──
    EOF = auto()
    ERROR = auto()
    NEWLINE = auto()

    # ── Girinti (Indentation) ──
    INDENT = auto()       # Girinti arttı
    DEDENT = auto()       # Girinti azaldı

    # ── Literaller ──
    INTEGER = auto()      # 42
    HEX_INTEGER = auto()  # 0xFF
    BINARY_INT = auto()   # 0b1010
    OCTAL_INT = auto()    # 0o77
    FLOAT = auto()        # 3.14
    STRING = auto()       # "hello"
    RAW_STRING = auto()   # r"raw\nstring"
    BYTE_STRING = auto()  # b"\x41\x42"
    CHAR = auto()         # 'c'
    FSTRING = auto()      # f"hello {name}"
    BOOL_TRUE = auto()    # true
    BOOL_FALSE = auto()   # false
    NULL = auto()         # null

    # ── Tanımlayıcılar ──
    IDENTIFIER = auto()   # my_variable
    TYPE_IDENT = auto()   # PascalCase type

    # ── MRR Özel Yapılar ──
    FONCTION_CREATE = auto()  # Fonction.create
    ADD_CODE = auto()         # add.code
    MRR_RUN = auto()          # mrr.run
    MRR_DEBUG = auto()        # mrr.debug

    # ── Anahtar Kelimeler: Kontrol Akışı ──
    KW_IF = auto()
    KW_ELIF = auto()
    KW_ELSE = auto()
    KW_MATCH = auto()
    KW_FOR = auto()
    KW_WHILE = auto()
    KW_LOOP = auto()
    KW_BREAK = auto()
    KW_CONTINUE = auto()
    KW_RETURN = auto()
    KW_YIELD = auto()
    KW_IN = auto()
    KW_PASS = auto()
    KW_FN = auto()

    # ── Anahtar Kelimeler: Bildirimler ──
    KW_LET = auto()
    KW_MUT = auto()
    KW_CONST = auto()
    KW_STATIC = auto()
    KW_STRUCT = auto()
    KW_ENUM = auto()
    KW_TRAIT = auto()
    KW_IMPL = auto()
    KW_MODULE = auto()
    KW_USE = auto()
    KW_PUB = auto()
    KW_PRIV = auto()
    KW_TYPE = auto()
    KW_CLASS = auto()

    # ── Anahtar Kelimeler: Bellek ve İşaretçi ──
    KW_UNSAFE = auto()
    KW_RAW = auto()
    KW_REF = auto()
    KW_OWN = auto()
    KW_DROP = auto()
    KW_ALLOC = auto()
    KW_STACK = auto()
    KW_PIN = auto()
    KW_VOLATILE = auto()
    KW_ALIGN = auto()

    # ── Anahtar Kelimeler: Siber Güvenlik / Ring-0 ──
    KW_KERNEL = auto()
    KW_RING0 = auto()
    KW_SYSCALL = auto()
    KW_INTERRUPT = auto()
    KW_PORT = auto()
    KW_ASM = auto()
    KW_SHELLCODE = auto()
    KW_INJECT = auto()
    KW_HOOK = auto()
    KW_DRIVER = auto()
    KW_EXPLOIT = auto()

    # ── Anahtar Kelimeler: Tipler ──
    KW_I8 = auto()
    KW_I16 = auto()
    KW_I32 = auto()
    KW_I64 = auto()
    KW_U8 = auto()
    KW_U16 = auto()
    KW_U32 = auto()
    KW_U64 = auto()
    KW_F32 = auto()
    KW_F64 = auto()
    KW_BOOL = auto()
    KW_STR = auto()
    KW_VOID = auto()
    KW_PTR = auto()
    KW_BYTE = auto()

    # ── Anahtar Kelimeler: Hata Yakalama ──
    KW_TRY = auto()
    KW_CATCH = auto()
    KW_FINALLY = auto()
    KW_THROW = auto()

    # ── Anahtar Kelimeler: Ek Kontrol ──
    KW_DELETE = auto()
    KW_FROM = auto()
    KW_WHERE = auto()
    KW_DO = auto()

    # ── Anahtar Kelimeler: Diğer ──
    KW_SELF = auto()
    KW_SUPER = auto()
    KW_AS = auto()
    KW_IS = auto()
    KW_NOT = auto()
    KW_AND = auto()
    KW_OR = auto()
    KW_ASYNC = auto()
    KW_AWAIT = auto()
    KW_DEFER = auto()
    KW_PRINT = auto()
    KW_PRINTLN = auto()
    KW_INPUT = auto()

    # ── Yeni Anahtar Kelimeler (MRR Core 10 Innovations) ──
    KW_TEMPORAL = auto()       # Time-Travel Debugging
    KW_SHARED = auto()         # Network-Transparent Variables
    KW_SECURE = auto()         # Post-Quantum Native Encryption
    KW_HW_POLYMORPH = auto()   # Hardware-Aware Polymorphism
    TYPE_UNTRUSTED = auto()    # SecTypes
    TYPE_SAFE = auto()         # SecTypes

    # ── Operatörler: Aritmetik ──
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %
    DOUBLE_STAR = auto()    # **

    # ── Operatörler: Bitwise ──
    AMPERSAND = auto()      # &
    PIPE = auto()           # |
    CARET = auto()          # ^
    TILDE = auto()          # ~
    SHIFT_LEFT = auto()     # <<
    SHIFT_RIGHT = auto()    # >>

    # ── Operatörler: Karşılaştırma ──
    EQUAL = auto()          # ==
    NOT_EQUAL = auto()      # !=
    LESS = auto()           # <
    GREATER = auto()        # >
    LESS_EQUAL = auto()     # <=
    GREATER_EQUAL = auto()  # >=

    # ── Operatörler: Atama ──
    ASSIGN = auto()         # =
    PLUS_ASSIGN = auto()    # +=
    MINUS_ASSIGN = auto()   # -=
    STAR_ASSIGN = auto()    # *=
    SLASH_ASSIGN = auto()   # /=
    PERCENT_ASSIGN = auto() # %=
    AMP_ASSIGN = auto()     # &=
    PIPE_ASSIGN = auto()    # |=
    CARET_ASSIGN = auto()   # ^=
    SHIFT_LEFT_ASSIGN = auto()   # <<=
    SHIFT_RIGHT_ASSIGN = auto()  # >>=
    DOUBLE_STAR_ASSIGN = auto()  # **=

    # ── Operatörler: Mantıksal ──
    LOGICAL_AND = auto()    # &&
    LOGICAL_OR = auto()     # ||
    BANG = auto()            # !

    # ── Operatörler: Özel ──
    NULL_COALESCE = auto()  # ??
    PIPE_OPERATOR = auto()  # |>

    # ── Operatörler: İşaretçi ──
    ARROW = auto()          # ->
    FAT_ARROW = auto()      # =>
    DOUBLE_COLON = auto()   # ::
    DOT = auto()            # .
    DOT_DOT = auto()        # ..
    ELLIPSIS = auto()       # ...
    AT = auto()             # @
    HASH = auto()           # #

    # ── Sınırlayıcılar ──
    LEFT_PAREN = auto()     # (
    RIGHT_PAREN = auto()    # )
    LEFT_BRACE = auto()     # {
    RIGHT_BRACE = auto()    # }
    LEFT_BRACKET = auto()   # [
    RIGHT_BRACKET = auto()  # ]
    SEMICOLON = auto()      # ;
    COLON = auto()          # :
    COMMA = auto()          # ,
    QUESTION = auto()       # ?


# ═══════════════════════════════════════════════════════════
# ─── TOKEN VERİ YAPISI ────────────────────────────────────
# ═══════════════════════════════════════════════════════════

@dataclass
class SourceLocation:
    """Kaynak dosyasındaki konum bilgisi."""
    file: str = "<stdin>"
    line: int = 1
    column: int = 1
    offset: int = 0

    def __str__(self) -> str:
        return f"{self.file}:{self.line}:{self.column}"


@dataclass
class Token:
    """Tek bir sözcüksel birim (token)."""
    type: TokenType
    lexeme: str
    location: SourceLocation = field(default_factory=SourceLocation)
    value: object = None  # Literal değer (int, float, str, bool)

    def __repr__(self) -> str:
        val = f" = {self.value!r}" if self.value is not None else ""
        return f"Token({self.type.name}, {self.lexeme!r}{val}, {self.location})"


# ═══════════════════════════════════════════════════════════
# ─── ANAHTAR KELİME HARİTASI ──────────────────────────────
# ═══════════════════════════════════════════════════════════

KEYWORDS: dict[str, TokenType] = {
    # Kontrol akışı
    "if":        TokenType.KW_IF,
    "elif":      TokenType.KW_ELIF,
    "otherwise": TokenType.KW_ELSE,
    "match":     TokenType.KW_MATCH,
    "for":       TokenType.KW_FOR,
    "loop":      TokenType.KW_LOOP,
    "break":     TokenType.KW_BREAK,
    "continue":  TokenType.KW_CONTINUE,
    "return":    TokenType.KW_RETURN,
    "yield":     TokenType.KW_YIELD,
    "in":        TokenType.KW_IN,
    "pass":      TokenType.KW_PASS,
    "fn":        TokenType.KW_FN,

    # Bildirimler
    "let":       TokenType.KW_LET,
    "mut":       TokenType.KW_MUT,
    "const":     TokenType.KW_CONST,
    "static":    TokenType.KW_STATIC,
    "struct":    TokenType.KW_STRUCT,
    "enum":      TokenType.KW_ENUM,
    "trait":     TokenType.KW_TRAIT,
    "impl":      TokenType.KW_IMPL,
    "module":    TokenType.KW_MODULE,
    "use":       TokenType.KW_USE,
    "pub":       TokenType.KW_PUB,
    "priv":      TokenType.KW_PRIV,
    "type":      TokenType.KW_TYPE,
    "class":     TokenType.KW_CLASS,

    # Bellek
    "unsafe":    TokenType.KW_UNSAFE,
    "raw":       TokenType.KW_RAW,
    "ref":       TokenType.KW_REF,
    "own":       TokenType.KW_OWN,
    "drop":      TokenType.KW_DROP,
    "alloc":     TokenType.KW_ALLOC,
    "stack":     TokenType.KW_STACK,
    "pin":       TokenType.KW_PIN,
    "volatile":  TokenType.KW_VOLATILE,
    "align":     TokenType.KW_ALIGN,

    # Siber güvenlik / Ring-0
    "kernel":    TokenType.KW_KERNEL,
    "ring0":     TokenType.KW_RING0,
    "syscall":   TokenType.KW_SYSCALL,
    "interrupt": TokenType.KW_INTERRUPT,
    "port":      TokenType.KW_PORT,
    "asm":       TokenType.KW_ASM,
    "shellcode": TokenType.KW_SHELLCODE,
    "inject":    TokenType.KW_INJECT,
    "hook":      TokenType.KW_HOOK,
    "driver":    TokenType.KW_DRIVER,
    "exploit":   TokenType.KW_EXPLOIT,

    # Tipler
    "i8":        TokenType.KW_I8,
    "i16":       TokenType.KW_I16,
    "i32":       TokenType.KW_I32,
    "i64":       TokenType.KW_I64,
    "u8":        TokenType.KW_U8,
    "u16":       TokenType.KW_U16,
    "u32":       TokenType.KW_U32,
    "u64":       TokenType.KW_U64,
    "f32":       TokenType.KW_F32,
    "f64":       TokenType.KW_F64,
    "bool":      TokenType.KW_BOOL,
    "str":       TokenType.KW_STR,
    "void":      TokenType.KW_VOID,
    "ptr":       TokenType.KW_PTR,
    "byte":      TokenType.KW_BYTE,

    # Hata yakalama
    "try":       TokenType.KW_TRY,
    "catch":     TokenType.KW_CATCH,
    "finally":   TokenType.KW_FINALLY,
    "throw":     TokenType.KW_THROW,

    # Ek kontrol
    "delete":    TokenType.KW_DELETE,
    "from":      TokenType.KW_FROM,
    "where":     TokenType.KW_WHERE,
    "do":        TokenType.KW_DO,

    # Diğer
    "true":      TokenType.BOOL_TRUE,
    "false":     TokenType.BOOL_FALSE,
    "null":      TokenType.NULL,
    "self":      TokenType.KW_SELF,
    "super":     TokenType.KW_SUPER,
    "as":        TokenType.KW_AS,
    "is":        TokenType.KW_IS,
    "not":       TokenType.KW_NOT,
    "and":       TokenType.KW_AND,
    "or":        TokenType.KW_OR,
    "async":     TokenType.KW_ASYNC,
    "await":     TokenType.KW_AWAIT,
    "defer":     TokenType.KW_DEFER,
    "print":     TokenType.KW_PRINT,
    "println":   TokenType.KW_PRINTLN,
    "input":     TokenType.KW_INPUT,

    # Core 10 Innovations Keywords
    "temporal":     TokenType.KW_TEMPORAL,
    "shared":       TokenType.KW_SHARED,
    "secure":       TokenType.KW_SECURE,
    "hw_polymorph": TokenType.KW_HW_POLYMORPH,
    "Untrusted":    TokenType.TYPE_UNTRUSTED,
    "Safe":         TokenType.TYPE_SAFE,
}

# MRR özel yapılar (dot-notation komutları)
# v1.0.1: Tüm anahtarlar lowercase — lookup sırasında .lower() ile normalize edilir
MRR_COMMANDS: dict[str, TokenType] = {
    "fonction.create": TokenType.FONCTION_CREATE,
    "function.create": TokenType.FONCTION_CREATE,
    "add.code":        TokenType.ADD_CODE,
    "mrr.run":         TokenType.MRR_RUN,
    "mrr.debug":       TokenType.MRR_DEBUG,
    "return.code":     TokenType.KW_WHILE,
}


# ═══════════════════════════════════════════════════════════
# ─── LEXER (SÖZCÜKSEL ÇÖZÜMLEYİCİ) ──────────────────────
# ═══════════════════════════════════════════════════════════

class LexerError(Exception):
    """Sözcüksel analiz hatası."""
    def __init__(self, message: str, location: SourceLocation):
        self.location = location
        super().__init__(f"{location}: {message}")


class Lexer:
    """
    MRR Lexer — Kaynak kodu token akışına dönüştürür.
    
    Python benzeri girinti takibi (INDENT/DEDENT) yapar.
    MRR'ye özgü Fonction.create ve add.code yapılarını tanır.
    
    v1.0.1: Case-insensitive komut/keyword tanıma, BOM desteği,
            gelişmiş hata kurtarma mekanizması.
    """

    def __init__(self, source: str, filename: str = "<stdin>"):
        # v1.0.1: BOM karakterini temizle
        if source.startswith('\ufeff'):
            source = source[1:]
        self._source = source
        self._filename = filename
        self._pos = 0
        self._line = 1
        self._column = 1
        self._tokens: List[Token] = []
        self._errors: List[LexerError] = []
        self._warnings: List[str] = []  # v1.0.1: Uyarı listesi (case hatası vb.)

        # ── Girinti takibi (Python-style) ──
        self._indent_stack: List[int] = [0]
        self._at_line_start = True
        self._paren_depth = 0  # (), [], {} içinde indent yok sayılır

    # ─────────────────────────────────────────────────────
    # Genel API
    # ─────────────────────────────────────────────────────

    @property
    def warnings(self) -> List[str]:
        """v1.0.1: Lexer uyarıları (case düzeltmeleri vb.)"""
        return self._warnings

    def tokenize(self) -> List[Token]:
        """Tüm kaynak kodu tokenize et ve token listesi döndür."""
        self._tokens = []
        self._pos = 0
        self._line = 1
        self._column = 1
        self._indent_stack = [0]
        self._at_line_start = True
        self._paren_depth = 0
        self._warnings = []

        while not self._is_at_end():
            self._scan_token()

        # Dosya sonu — kalan DEDENT'leri ekle
        while len(self._indent_stack) > 1:
            self._indent_stack.pop()
            self._emit(TokenType.DEDENT, "")

        self._emit(TokenType.EOF, "")
        return self._tokens

    @property
    def errors(self) -> List[LexerError]:
        return self._errors

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0

    # ─────────────────────────────────────────────────────
    # Karakter Tarama
    # ─────────────────────────────────────────────────────

    def _is_at_end(self) -> bool:
        return self._pos >= len(self._source)

    def _peek(self) -> str:
        if self._is_at_end():
            return "\0"
        return self._source[self._pos]

    def _peek_next(self) -> str:
        if self._pos + 1 >= len(self._source):
            return "\0"
        return self._source[self._pos + 1]

    def _peek_at(self, offset: int) -> str:
        idx = self._pos + offset
        if idx >= len(self._source):
            return "\0"
        return self._source[idx]

    def _advance(self) -> str:
        c = self._source[self._pos]
        self._pos += 1
        if c == "\n":
            self._line += 1
            self._column = 1
        else:
            self._column += 1
        return c

    def _match(self, expected: str) -> bool:
        if self._is_at_end() or self._source[self._pos] != expected:
            return False
        self._advance()
        return True

    def _current_loc(self) -> SourceLocation:
        return SourceLocation(self._filename, self._line, self._column, self._pos)

    # ─────────────────────────────────────────────────────
    # Token Üretimi
    # ─────────────────────────────────────────────────────

    def _emit(self, token_type: TokenType, lexeme: str,
              loc: Optional[SourceLocation] = None,
              value: object = None) -> None:
        if loc is None:
            loc = self._current_loc()
        self._tokens.append(Token(token_type, lexeme, loc, value))

    def _emit_error(self, message: str, loc: Optional[SourceLocation] = None) -> None:
        if loc is None:
            loc = self._current_loc()
        err = LexerError(message, loc)
        self._errors.append(err)
        self._emit(TokenType.ERROR, message, loc)

    # ─────────────────────────────────────────────────────
    # Ana Tarama Döngüsü
    # ─────────────────────────────────────────────────────

    def _scan_token(self) -> None:
        # v1.0.1: Tüm tarama try/except ile sarılır — tek bir hatalı karakter
        # lexer'ı çökertmez, ERROR token üretilir ve taramaya devam edilir.
        try:
            self._scan_token_inner()
        except Exception as e:
            loc = self._current_loc()
            self._emit_error(f"Beklenmeyen lexer hatası: {e}", loc)
            # Sonsuz döngüyü önlemek için en az bir karakter atla
            if not self._is_at_end():
                self._advance()

    def _scan_token_inner(self) -> None:
        """v1.0.1: Asıl tarama mantığı — _scan_token tarafından güvenli sarılır."""
        # ── Satır başı girinti kontrolü ──
        if self._at_line_start and self._paren_depth == 0:
            self._handle_indentation()
            self._at_line_start = False

        c = self._peek()

        # ── Boşluk (satır içi) ──
        if c in (" ", "\t", "\r"):
            self._advance()
            return

        # ── Yeni satır ──
        if c == "\n":
            self._advance()
            if self._paren_depth == 0:
                self._emit(TokenType.NEWLINE, "\\n")
                self._at_line_start = True
            return

        # ── Yorumlar ──
        if c == "/" and self._peek_next() == "/":
            self._skip_line_comment()
            return
        if c == "/" and self._peek_next() == "*":
            self._skip_block_comment()
            return
        if c == "#" and self._peek_next() not in ("[",):
            # Tek satırlık Python-style yorum
            self._skip_line_comment()
            return

        loc = self._current_loc()

        # ── Sayısal literaller ──
        if c.isdigit():
            self._scan_number(loc)
            return

        # ── String literaller ──
        if c == '"':
            self._scan_string(loc)
            return
        if c == "'" :
            self._scan_char(loc)
            return
        if c in ("r", "b", "f") and self._peek_next() == '"':
            self._scan_prefixed_string(loc)
            return

        # ── Tanımlayıcılar / Anahtar kelimeler / MRR komutları ──
        if c.isalpha() or c == "_":
            self._scan_identifier(loc)
            return

        # ── Operatörler ve sınırlayıcılar ──
        self._scan_operator(loc)

    # ─────────────────────────────────────────────────────
    # Girinti Yönetimi (Python-style INDENT/DEDENT)
    # ─────────────────────────────────────────────────────

    def _handle_indentation(self) -> None:
        """Satır başındaki boşlukları ölç ve INDENT/DEDENT üret."""
        indent = 0
        while not self._is_at_end() and self._peek() in (" ", "\t"):
            if self._peek() == "\t":
                indent += 4  # Tab = 4 boşluk
            else:
                indent += 1
            self._advance()

        # Boş satır veya yorum satırı — indent değişikliği yapma
        if self._is_at_end() or self._peek() == "\n" or \
           (self._peek() == "/" and self._peek_next() == "/") or \
           (self._peek() == "#" and self._peek_next() != "["):
            return

        current_indent = self._indent_stack[-1]

        if indent > current_indent:
            self._indent_stack.append(indent)
            self._emit(TokenType.INDENT, " " * indent)
        elif indent < current_indent:
            while len(self._indent_stack) > 1 and self._indent_stack[-1] > indent:
                self._indent_stack.pop()
                self._emit(TokenType.DEDENT, "")
            if self._indent_stack[-1] != indent:
                self._emit_error(
                    f"Tutarsız girinti: beklenen {self._indent_stack[-1]}, "
                    f"bulunan {indent}")

    # ─────────────────────────────────────────────────────
    # Yorum Atlama
    # ─────────────────────────────────────────────────────

    def _skip_line_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _skip_block_comment(self) -> None:
        self._advance()  # /
        self._advance()  # *
        depth = 1
        while not self._is_at_end() and depth > 0:
            if self._peek() == "/" and self._peek_next() == "*":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                depth -= 1
            else:
                self._advance()

    # ─────────────────────────────────────────────────────
    # Sayısal Literal Tarama
    # ─────────────────────────────────────────────────────

    def _scan_number(self, loc: SourceLocation) -> None:
        start = self._pos
        c = self._peek()

        # Özel tabanlar: 0x, 0b, 0o
        if c == "0" and self._peek_next() in ("x", "X"):
            self._advance()  # 0
            self._advance()  # x
            while not self._is_at_end() and (self._peek() in "0123456789abcdefABCDEF_"):
                self._advance()
            lexeme = self._source[start:self._pos]
            value = int(lexeme.replace("_", ""), 16)
            self._emit(TokenType.HEX_INTEGER, lexeme, loc, value)
            return

        if c == "0" and self._peek_next() in ("b", "B"):
            self._advance()
            self._advance()
            while not self._is_at_end() and self._peek() in "01_":
                self._advance()
            lexeme = self._source[start:self._pos]
            value = int(lexeme.replace("_", ""), 2)
            self._emit(TokenType.BINARY_INT, lexeme, loc, value)
            return

        if c == "0" and self._peek_next() in ("o", "O"):
            self._advance()
            self._advance()
            while not self._is_at_end() and self._peek() in "01234567_":
                self._advance()
            lexeme = self._source[start:self._pos]
            value = int(lexeme.replace("_", ""), 8)
            self._emit(TokenType.OCTAL_INT, lexeme, loc, value)
            return

        # Ondalıklı veya tam sayı
        is_float = False
        while not self._is_at_end() and (self._peek().isdigit() or self._peek() == "_"):
            self._advance()

        if not self._is_at_end() and self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()  # .
            while not self._is_at_end() and (self._peek().isdigit() or self._peek() == "_"):
                self._advance()

        # Bilimsel gösterim: 1e5, 1.5e-3
        if not self._is_at_end() and self._peek() in ("e", "E"):
            is_float = True
            self._advance()
            if not self._is_at_end() and self._peek() in ("+", "-"):
                self._advance()
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        lexeme = self._source[start:self._pos]
        clean = lexeme.replace("_", "")

        if is_float:
            self._emit(TokenType.FLOAT, lexeme, loc, float(clean))
        else:
            self._emit(TokenType.INTEGER, lexeme, loc, int(clean))

    # ─────────────────────────────────────────────────────
    # String Literal Tarama
    # ─────────────────────────────────────────────────────

    def _scan_string(self, loc: SourceLocation) -> None:
        self._advance()  # açılış "
        result = []

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\\":
                result.append(self._process_escape())
            elif self._peek() == "#" and self._peek_next() == "{":
                # String interpolation: #{expr}
                result.append(self._peek())
                self._advance()
                result.append(self._peek())
                self._advance()
                depth = 1
                while not self._is_at_end() and depth > 0:
                    if self._peek() == "{":
                        depth += 1
                    elif self._peek() == "}":
                        depth -= 1
                    result.append(self._peek())
                    self._advance()
                continue
            else:
                result.append(self._advance())

        if self._is_at_end():
            self._emit_error("Sonlandırılmamış string literali", loc)
            return

        self._advance()  # kapanış "
        value = "".join(result)
        self._emit(TokenType.STRING, f'"{value}"', loc, value)

    def _scan_char(self, loc: SourceLocation) -> None:
        self._advance()  # '
        if self._peek() == "\\":
            value = self._process_escape()
        else:
            value = self._advance()

        if not self._is_at_end() and self._peek() == "'":
            self._advance()
        else:
            self._emit_error("Sonlandırılmamış karakter literali", loc)
            return

        self._emit(TokenType.CHAR, f"'{value}'", loc, value)

    def _scan_prefixed_string(self, loc: SourceLocation) -> None:
        prefix = self._advance()  # r, b, veya f
        self._advance()  # "
        result = []

        while not self._is_at_end() and self._peek() != '"':
            if prefix == "r":
                # Raw string — escape yok
                result.append(self._advance())
            elif self._peek() == "\\":
                if prefix == "b":
                    result.append(self._process_escape())
                else:
                    result.append(self._process_escape())
            else:
                result.append(self._advance())

        if self._is_at_end():
            self._emit_error("Sonlandırılmamış string literali", loc)
            return

        self._advance()  # kapanış "
        value = "".join(result)

        if prefix == "r":
            self._emit(TokenType.RAW_STRING, f'r"{value}"', loc, value)
        elif prefix == "b":
            byte_val = value.encode("latin-1", errors="replace")
            self._emit(TokenType.BYTE_STRING, f'b"{value}"', loc, byte_val)
        elif prefix == "f":
            self._emit(TokenType.FSTRING, f'f"{value}"', loc, value)

    def _process_escape(self) -> str:
        self._advance()  # backslash
        if self._is_at_end():
            return "\\"
        c = self._advance()
        escape_map = {
            "n": "\n", "t": "\t", "r": "\r", "0": "\0",
            "\\": "\\", '"': '"', "'": "'", "a": "\a",
            "b": "\b", "f": "\f", "v": "\v",
        }
        if c in escape_map:
            return escape_map[c]
        if c == "x":
            # \xHH
            hex_str = ""
            for _ in range(2):
                if not self._is_at_end() and self._peek() in "0123456789abcdefABCDEF":
                    hex_str += self._advance()
            return chr(int(hex_str, 16)) if hex_str else "\\x"
        return "\\" + c

    # ─────────────────────────────────────────────────────
    # Tanımlayıcı / Anahtar Kelime / MRR Komutu Tarama
    # ─────────────────────────────────────────────────────

    def _scan_identifier(self, loc: SourceLocation) -> None:
        start = self._pos
        while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
            self._advance()

        word = self._source[start:self._pos]

        # ── MRR özel komutları: Fonction.create, add.code, vb. ──
        # v1.0.1: Case-insensitive komut tanıma
        if not self._is_at_end() and self._peek() == ".":
            # "Fonction.create" veya "add.code" olabilir
            save_pos = self._pos
            save_line = self._line
            save_col = self._column
            self._advance()  # .
            ext_start = self._pos
            while not self._is_at_end() and (self._peek().isalnum() or self._peek() == "_"):
                self._advance()
            ext_word = self._source[ext_start:self._pos]
            full_command = f"{word}.{ext_word}"
            full_command_lower = full_command.lower()  # v1.0.1: Normalize

            if full_command_lower in MRR_COMMANDS:
                # v1.0.1: Doğru yazımı kontrol et, yanlışsa uyarı üret
                canonical_forms = {
                    "fonction.create": "Fonction.create",
                    "function.create": "Function.create",
                    "add.code": "add.code",
                    "mrr.run": "mrr.run",
                    "mrr.debug": "mrr.debug",
                    "return.code": "return.code",
                }
                canonical = canonical_forms.get(full_command_lower, full_command)
                if full_command != canonical:
                    self._warnings.append(
                        f"{loc}: Büyük/küçük harf uyarısı: '{full_command}' → doğrusu '{canonical}'"
                    )
                self._emit(MRR_COMMANDS[full_command_lower], full_command, loc)
                return
            else:
                # MRR komutu değil — geri al, sadece tanımlayıcı + DOT
                self._pos = save_pos
                self._line = save_line
                self._column = save_col

        # ── Anahtar kelime mi? ──
        # v1.0.1: Case-insensitive anahtar kelime tanıma
        word_lower = word.lower()
        if word_lower in KEYWORDS:
            # Doğru yazım kontrolü — uyarı üret
            if word != word_lower and word_lower in KEYWORDS:
                self._warnings.append(
                    f"{loc}: Büyük/küçük harf uyarısı: '{word}' → doğrusu '{word_lower}'"
                )
            self._emit(KEYWORDS[word_lower], word, loc,
                       True if word_lower == "true" else
                       False if word_lower == "false" else
                       None if word_lower == "null" else None)
            return

        # ── PascalCase → tip tanımlayıcı ──
        if word[0].isupper() and not word.isupper():
            self._emit(TokenType.TYPE_IDENT, word, loc, word)
        else:
            self._emit(TokenType.IDENTIFIER, word, loc, word)

    # ─────────────────────────────────────────────────────
    # Operatör ve Sınırlayıcı Tarama
    # ─────────────────────────────────────────────────────

    def _scan_operator(self, loc: SourceLocation) -> None:
        c = self._advance()

        match c:
            # Tek karakterli
            case "(":
                self._paren_depth += 1
                self._emit(TokenType.LEFT_PAREN, "(", loc)
            case ")":
                self._paren_depth = max(0, self._paren_depth - 1)
                self._emit(TokenType.RIGHT_PAREN, ")", loc)
            case "{":
                self._paren_depth += 1
                self._emit(TokenType.LEFT_BRACE, "{", loc)
            case "}":
                self._paren_depth = max(0, self._paren_depth - 1)
                self._emit(TokenType.RIGHT_BRACE, "}", loc)
            case "[":
                self._paren_depth += 1
                self._emit(TokenType.LEFT_BRACKET, "[", loc)
            case "]":
                self._paren_depth = max(0, self._paren_depth - 1)
                self._emit(TokenType.RIGHT_BRACKET, "]", loc)
            case ";":
                self._emit(TokenType.SEMICOLON, ";", loc)
            case ",":
                self._emit(TokenType.COMMA, ",", loc)
            case "~":
                self._emit(TokenType.TILDE, "~", loc)
            case "?":
                if self._match("?"):
                    self._emit(TokenType.NULL_COALESCE, "??", loc)
                else:
                    self._emit(TokenType.QUESTION, "?", loc)
            case "@":
                self._emit(TokenType.AT, "@", loc)

            # Çift karakterli olabilenler
            case ":":
                if self._match(":"):
                    self._emit(TokenType.DOUBLE_COLON, "::", loc)
                else:
                    self._emit(TokenType.COLON, ":", loc)
            case ".":
                if self._match("."):
                    if self._match("."):
                        self._emit(TokenType.ELLIPSIS, "...", loc)
                    else:
                        self._emit(TokenType.DOT_DOT, "..", loc)
                else:
                    self._emit(TokenType.DOT, ".", loc)
            case "+":
                if self._match("="):
                    self._emit(TokenType.PLUS_ASSIGN, "+=", loc)
                else:
                    self._emit(TokenType.PLUS, "+", loc)
            case "-":
                if self._match(">"):
                    self._emit(TokenType.ARROW, "->", loc)
                elif self._match("="):
                    self._emit(TokenType.MINUS_ASSIGN, "-=", loc)
                else:
                    self._emit(TokenType.MINUS, "-", loc)
            case "*":
                if self._match("*"):
                    if self._match("="):
                        self._emit(TokenType.DOUBLE_STAR_ASSIGN, "**=", loc)
                    else:
                        self._emit(TokenType.DOUBLE_STAR, "**", loc)
                elif self._match("="):
                    self._emit(TokenType.STAR_ASSIGN, "*=", loc)
                else:
                    self._emit(TokenType.STAR, "*", loc)
            case "/":
                if self._match("="):
                    self._emit(TokenType.SLASH_ASSIGN, "/=", loc)
                else:
                    self._emit(TokenType.SLASH, "/", loc)
            case "%":
                if self._match("="):
                    self._emit(TokenType.PERCENT_ASSIGN, "%=", loc)
                else:
                    self._emit(TokenType.PERCENT, "%", loc)
            case "=":
                if self._match("="):
                    self._emit(TokenType.EQUAL, "==", loc)
                elif self._match(">"):
                    self._emit(TokenType.FAT_ARROW, "=>", loc)
                else:
                    self._emit(TokenType.ASSIGN, "=", loc)
            case "!":
                if self._match("="):
                    self._emit(TokenType.NOT_EQUAL, "!=", loc)
                else:
                    self._emit(TokenType.BANG, "!", loc)
            case "<":
                if self._match("<"):
                    if self._match("="):
                        self._emit(TokenType.SHIFT_LEFT_ASSIGN, "<<=", loc)
                    else:
                        self._emit(TokenType.SHIFT_LEFT, "<<", loc)
                elif self._match("="):
                    self._emit(TokenType.LESS_EQUAL, "<=", loc)
                else:
                    self._emit(TokenType.LESS, "<", loc)
            case ">":
                if self._match(">"):
                    if self._match("="):
                        self._emit(TokenType.SHIFT_RIGHT_ASSIGN, ">>=", loc)
                    else:
                        self._emit(TokenType.SHIFT_RIGHT, ">>", loc)
                elif self._match("="):
                    self._emit(TokenType.GREATER_EQUAL, ">=", loc)
                else:
                    self._emit(TokenType.GREATER, ">", loc)
            case "&":
                if self._match("&"):
                    self._emit(TokenType.LOGICAL_AND, "&&", loc)
                elif self._match("="):
                    self._emit(TokenType.AMP_ASSIGN, "&=", loc)
                else:
                    self._emit(TokenType.AMPERSAND, "&", loc)
            case "|":
                if self._match(">"):
                    self._emit(TokenType.PIPE_OPERATOR, "|>", loc)
                elif self._match("|"):
                    self._emit(TokenType.LOGICAL_OR, "||", loc)
                elif self._match("="):
                    self._emit(TokenType.PIPE_ASSIGN, "|=", loc)
                else:
                    self._emit(TokenType.PIPE, "|", loc)
            case "^":
                if self._match("="):
                    self._emit(TokenType.CARET_ASSIGN, "^=", loc)
                else:
                    self._emit(TokenType.CARET, "^", loc)
            case "#":
                if self._match("["):
                    # Attribute: #[...] — bunu identifier olarak bırak
                    self._emit(TokenType.HASH, "#[", loc)
                else:
                    self._emit(TokenType.HASH, "#", loc)
            case _:
                self._emit_error(f"Beklenmeyen karakter: '{c}'", loc)
