"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Parser — Sözdizimsel Çözümleyici v1.0.1 Resilient         ║
║                                                                  ║
║  Token akışını AST'ye (Abstract Syntax Tree) dönüştürür.        ║
║  Recursive Descent + Precedence Climbing hibrit parser.         ║
║                                                                  ║
║  v1.0.1: Gelişmiş hata kurtarma, toleranslı sözdizimi,          ║
║          eksik ':' toleransı, daha iyi hata mesajları.           ║
║                                                                  ║
║  Desteklenen yapılar:                                           ║
║    - Fonction.create "isim" (params):  → Fonksiyon tanımlama    ║
║    - add.code "kütüphane"              → FFI import              ║
║    - let / mut                         → Değişken bağlama       ║
║    - if / elif / else / match          → Kontrol akışı          ║
║    - for / while / loop                → Döngüler               ║
║    - struct / trait / impl / class     → Tip tanımlama          ║
║    - unsafe / kernel / ring0           → Güvenlik bağlamları    ║
║    - exploit / hook / driver           → Siber güvenlik blokları║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from interpreter.mrr_lexer import Token, TokenType, SourceLocation


# ═══════════════════════════════════════════════════════════
# ─── AST DÜĞÜM TİPLERİ ───────────────────────────────────
# ═══════════════════════════════════════════════════════════

# ── Program (Kök Düğüm) ──
@dataclass
class Program:
    """AST kök düğümü — bir MRR kaynak dosyasını temsil eder."""
    module_name: str = ""
    body: List[ASTNode] = field(default_factory=list)
    location: Optional[SourceLocation] = None


# ── Temel AST Düğüm ──
@dataclass
class ASTNode:
    """Tüm AST düğümlerinin temel sınıfı."""
    location: Optional[SourceLocation] = None


# ═══════════════════════════════════════════════════════════
# ─── İFADELER (EXPRESSIONS) ───────────────────────────────
# ═══════════════════════════════════════════════════════════

@dataclass
class LiteralExpr(ASTNode):
    """Sabit değer: sayı, string, bool, null."""
    value: Any = None
    literal_type: str = "unknown"  # "int", "float", "string", "bool", "null", "hex", "bytes"

@dataclass
class IdentifierExpr(ASTNode):
    """Tanımlayıcı: değişken veya fonksiyon adı."""
    name: str = ""

@dataclass
class BinaryExpr(ASTNode):
    """İkili işlem: a + b, x == y, vb."""
    left: Optional[ASTNode] = None
    operator: str = ""
    right: Optional[ASTNode] = None

@dataclass
class UnaryExpr(ASTNode):
    """Tekli işlem: -x, !flag, ~bits."""
    operator: str = ""
    operand: Optional[ASTNode] = None
    prefix: bool = True

@dataclass
class CallExpr(ASTNode):
    """Fonksiyon çağrısı: foo(a, b)."""
    callee: Optional[ASTNode] = None
    arguments: List[ASTNode] = field(default_factory=list)

@dataclass
class MemberAccessExpr(ASTNode):
    """Üye erişimi: obj.field veya obj::method."""
    object: Optional[ASTNode] = None
    member: str = ""
    is_static: bool = False  # :: kullanıldıysa True

@dataclass
class IndexExpr(ASTNode):
    """Dizi indeksleme: arr[i]."""
    object: Optional[ASTNode] = None
    index: Optional[ASTNode] = None

@dataclass
class CastExpr(ASTNode):
    """Tip dönüşümü: expr as Type."""
    operand: Optional[ASTNode] = None
    target_type: str = ""

@dataclass
class RangeExpr(ASTNode):
    """Aralık: start..end."""
    start: Optional[ASTNode] = None
    end: Optional[ASTNode] = None
    inclusive: bool = False  # ..= için True

@dataclass
class ListExpr(ASTNode):
    """Liste literali: [1, 2, 3]."""
    elements: List[ASTNode] = field(default_factory=list)

@dataclass
class DictExpr(ASTNode):
    """Sözlük literali: {key: value}."""
    pairs: List[tuple] = field(default_factory=list)  # [(key, value), ...]

@dataclass
class InterpolatedStringExpr(ASTNode):
    """String interpolation: "hello #{name}"."""
    parts: List[ASTNode] = field(default_factory=list)  # LiteralExpr ve diğerleri

@dataclass
class LambdaExpr(ASTNode):
    """Lambda / anonim fonksiyon: |x, y| => x + y."""
    params: List[Parameter] = field(default_factory=list)
    body: Optional[ASTNode] = None

@dataclass
class TupleExpr(ASTNode):
    """Tuple literali: (a, b, c)."""
    elements: List[ASTNode] = field(default_factory=list)

@dataclass
class AwaitExpr(ASTNode):
    """Await ifadesi: await foo()."""
    expression: Optional[ASTNode] = None

@dataclass
class AsmExpr(ASTNode):
    """Inline assembly: asm { ... }."""
    code: str = ""
    outputs: List[str] = field(default_factory=list)
    inputs: List[str] = field(default_factory=list)
    clobbers: List[str] = field(default_factory=list)

@dataclass
class ShellcodeExpr(ASTNode):
    """Shellcode bloğu: shellcode x86_64 { ... }."""
    arch: str = "x86_64"
    code: str = ""

@dataclass
class SyscallExpr(ASTNode):
    """Sistem çağrısı: syscall(nr, ...)."""
    number: Optional[ASTNode] = None
    args: List[ASTNode] = field(default_factory=list)

@dataclass
class AssignExpr(ASTNode):
    """Atama ifadesi: x = value, x += value."""
    target: Optional[ASTNode] = None
    operator: str = "="
    value: Optional[ASTNode] = None

@dataclass
class TernaryExpr(ASTNode):
    """Ternary ifade: condition ? true_val : false_val."""
    condition: Optional[ASTNode] = None
    true_value: Optional[ASTNode] = None
    false_value: Optional[ASTNode] = None

@dataclass
class PipeExpr(ASTNode):
    """Pipe operatörü: value |> fn1 |> fn2."""
    value: Optional[ASTNode] = None
    function: Optional[ASTNode] = None


# ═══════════════════════════════════════════════════════════
# ─── BİLDİRİMLER (STATEMENTS) ─────────────────────────────
# ═══════════════════════════════════════════════════════════

@dataclass
class Parameter:
    """Fonksiyon parametresi."""
    name: str = ""
    type_annotation: Optional[str] = None
    default_value: Optional[ASTNode] = None
    is_mut: bool = False

@dataclass
class FunctionDecl(ASTNode):
    """Fonksiyon tanımlama: Fonction.create 'isim' (params):"""
    name: str = ""
    params: List[Parameter] = field(default_factory=list)
    return_type: Optional[str] = None
    body: List[ASTNode] = field(default_factory=list)
    is_pub: bool = False
    is_unsafe: bool = False
    is_kernel: bool = False
    is_hw_polymorph: bool = False
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)

@dataclass
class VarDecl(ASTNode):
    """Değişken tanımlama: let x = 5 veya mut y: i32 = 10."""
    name: str = ""
    type_annotation: Optional[str] = None
    initializer: Optional[ASTNode] = None
    is_mutable: bool = False
    is_const: bool = False
    is_static: bool = False
    is_temporal: bool = False
    is_secure: bool = False
    shared_target: Optional[str] = None

@dataclass
class AddCodeDecl(ASTNode):
    """FFI kütüphane aktarımı: add.code 'numpy'."""
    library: str = ""
    alias: Optional[str] = None
    imports: List[str] = field(default_factory=list)  # Seçici import

@dataclass
class ModuleDecl(ASTNode):
    """Modül tanımlama: module my_module."""
    name: str = ""

@dataclass
class UseDecl(ASTNode):
    """Import: use std::io."""
    path: str = ""
    alias: Optional[str] = None

@dataclass
class StructDecl(ASTNode):
    """Struct tanımlama."""
    name: str = ""
    fields: List[Parameter] = field(default_factory=list)
    is_pub: bool = False
    is_packed: bool = False
    decorators: List[str] = field(default_factory=list)

@dataclass
class ClassDecl(ASTNode):
    """Sınıf tanımlama."""
    name: str = ""
    base_classes: List[str] = field(default_factory=list)
    body: List[ASTNode] = field(default_factory=list)
    is_pub: bool = False

@dataclass
class TraitDecl(ASTNode):
    """Trait tanımlama."""
    name: str = ""
    methods: List[FunctionDecl] = field(default_factory=list)
    is_pub: bool = False

@dataclass
class ImplDecl(ASTNode):
    """Implementasyon bloğu: impl Type { ... }."""
    type_name: str = ""
    trait_name: Optional[str] = None
    methods: List[FunctionDecl] = field(default_factory=list)

@dataclass
class ExploitDecl(ASTNode):
    """Exploit modülü: exploit Name { ... }."""
    name: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class DriverDecl(ASTNode):
    """Kernel driver: driver Name { ... }."""
    name: str = ""
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class HookDecl(ASTNode):
    """Fonksiyon hook: hook FuncName(type='inline') { ... }."""
    target: str = ""
    hook_type: str = "inline"
    body: List[ASTNode] = field(default_factory=list)


# ── Kontrol Akışı ──

@dataclass
class IfStmt(ASTNode):
    """If / elif / else bloğu."""
    condition: Optional[ASTNode] = None
    then_body: List[ASTNode] = field(default_factory=list)
    elif_clauses: List[tuple] = field(default_factory=list)  # [(condition, body), ...]
    else_body: List[ASTNode] = field(default_factory=list)

@dataclass
class ForStmt(ASTNode):
    """For döngüsü: for item in collection:"""
    variable: str = ""
    iterable: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class WhileStmt(ASTNode):
    """While döngüsü."""
    condition: Optional[ASTNode] = None
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class LoopStmt(ASTNode):
    """Sonsuz döngü: loop:"""
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class MatchStmt(ASTNode):
    """Pattern matching: match value:"""
    value: Optional[ASTNode] = None
    arms: List[tuple] = field(default_factory=list)  # [(pattern, body), ...]

@dataclass
class ReturnStmt(ASTNode):
    """Return ifadesi."""
    value: Optional[ASTNode] = None

@dataclass
class BreakStmt(ASTNode):
    """Break ifadesi."""
    pass

@dataclass
class ContinueStmt(ASTNode):
    """Continue ifadesi."""
    pass

@dataclass
class PassStmt(ASTNode):
    """Boş ifade (Python pass)."""
    pass

@dataclass
class UnsafeBlock(ASTNode):
    """Unsafe bloğu."""
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class KernelBlock(ASTNode):
    """Ring-0 kernel bloğu."""
    body: List[ASTNode] = field(default_factory=list)

@dataclass
class ExpressionStmt(ASTNode):
    """Bir ifadeyi deyim olarak çalıştır."""
    expression: Optional[ASTNode] = None

@dataclass
class PrintStmt(ASTNode):
    """print / println ifadesi."""
    value: Optional[ASTNode] = None
    newline: bool = True

@dataclass
class TryCatchStmt(ASTNode):
    """try / catch / finally bloğu."""
    try_body: List[ASTNode] = field(default_factory=list)
    catch_var: Optional[str] = None
    catch_body: List[ASTNode] = field(default_factory=list)
    finally_body: List[ASTNode] = field(default_factory=list)

@dataclass
class ThrowStmt(ASTNode):
    """throw ifadesi."""
    value: Optional[ASTNode] = None

@dataclass
class EnumDecl(ASTNode):
    """Enum tanımlama: enum Color: RED, GREEN, BLUE."""
    name: str = ""
    variants: List[tuple] = field(default_factory=list)  # [(name, value), ...]
    is_pub: bool = False

@dataclass
class DeleteStmt(ASTNode):
    """delete ifadesi: delete x veya delete arr[i]."""
    target: Optional[ASTNode] = None

@dataclass
class DoWhileStmt(ASTNode):
    """Do-while döngüsü: do: body return.code condition."""
    body: List[ASTNode] = field(default_factory=list)
    condition: Optional[ASTNode] = None

@dataclass
class DeferStmt(ASTNode):
    """Defer ifadesi — fonksiyon çıkışında çalıştırılır."""
    body: List[ASTNode] = field(default_factory=list)

# ═══════════════════════════════════════════════════════════
# ─── PARSER ───────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class ParseError(Exception):
    """Sözdizimi hatası."""
    def __init__(self, message: str, token: Token):
        self.token = token
        super().__init__(f"{token.location}: {message}")


class Parser:
    """
    MRR Recursive Descent Parser v1.0.1.
    
    Token akışını AST'ye dönüştürür.
    Girinti tabanlı blokları (INDENT/DEDENT) Python benzeri yönetir.
    
    v1.0.1: Gelişmiş hata kurtarma — eksik ':' toleransı,
            daha iyi senkronizasyon, boş blok toleransı.
    """

    def __init__(self, tokens: List[Token]):
        self._tokens = tokens
        self._pos = 0
        self._errors: List[ParseError] = []
        self._warnings: List[str] = []  # v1.0.1: Parser uyarıları

    # ─────────────────────────────────────────────────────
    # Genel API
    # ─────────────────────────────────────────────────────

    def parse(self) -> Program:
        """Tüm token akışını ayrıştır ve Program AST döndür."""
        program = Program(location=self._current().location)
        self._skip_newlines()

        while not self._is_at_end():
            try:
                node = self._parse_top_level()
                if node is not None:
                    program.body.append(node)
            except ParseError as e:
                self._errors.append(e)
                self._synchronize()
            self._skip_newlines()

        return program

    @property
    def errors(self) -> List[ParseError]:
        return self._errors

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0

    # ─────────────────────────────────────────────────────
    # Token Tüketimi
    # ─────────────────────────────────────────────────────

    def _current(self) -> Token:
        if self._pos < len(self._tokens):
            return self._tokens[self._pos]
        return Token(TokenType.EOF, "", SourceLocation())

    def _previous(self) -> Token:
        return self._tokens[max(0, self._pos - 1)]

    def _advance(self) -> Token:
        tok = self._current()
        if not self._is_at_end():
            self._pos += 1
        return tok

    def _check(self, *types: TokenType) -> bool:
        return self._current().type in types

    def _match(self, *types: TokenType) -> bool:
        if self._current().type in types:
            self._advance()
            return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise ParseError(message, self._current())

    def _is_at_end(self) -> bool:
        return self._current().type == TokenType.EOF

    def _skip_newlines(self) -> None:
        while self._check(TokenType.NEWLINE):
            self._advance()

    def _synchronize(self) -> None:
        """v1.0.1: Gelişmiş hata kurtarma — daha fazla senkronizasyon noktası."""
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.NEWLINE:
                return
            if self._current().type in (
                TokenType.FONCTION_CREATE, TokenType.KW_LET, TokenType.KW_MUT,
                TokenType.KW_IF, TokenType.KW_FOR, TokenType.KW_WHILE,
                TokenType.KW_RETURN, TokenType.ADD_CODE, TokenType.KW_STRUCT,
                TokenType.KW_CLASS, TokenType.KW_PUB, TokenType.DEDENT,
                # v1.0.1: Ek senkronizasyon noktaları
                TokenType.KW_FN, TokenType.KW_ENUM, TokenType.KW_TRAIT,
                TokenType.KW_IMPL, TokenType.KW_TRY, TokenType.KW_MATCH,
                TokenType.KW_LOOP, TokenType.KW_UNSAFE, TokenType.KW_KERNEL,
                TokenType.KW_EXPLOIT, TokenType.KW_DRIVER, TokenType.KW_HOOK,
                TokenType.KW_CONST, TokenType.KW_PRINT, TokenType.KW_PRINTLN,
                TokenType.KW_DO, TokenType.KW_DEFER, TokenType.KW_DELETE,
                TokenType.KW_THROW, TokenType.KW_BREAK, TokenType.KW_CONTINUE,
            ):
                return
            self._advance()

    def _consume_tolerant(self, token_type: TokenType, message: str) -> Optional[Token]:
        """v1.0.1: Toleranslı token tüketimi — eksikse uyarı verir ama çökmez."""
        if self._check(token_type):
            return self._advance()
        # Eksik token — uyarı üret ama devam et
        self._warnings.append(
            f"{self._current().location}: Uyarı: {message} (eksik, otomatik tamamlandı)"
        )
        return None

    # ─────────────────────────────────────────────────────
    # Girinti Tabanlı Blok Ayrıştırma
    # ─────────────────────────────────────────────────────

    def _parse_block(self) -> List[ASTNode]:
        """
        Girinti tabanlı blok ayrıştır.
        Bekler: NEWLINE INDENT <body> DEDENT
        """
        self._skip_newlines()
        body: List[ASTNode] = []

        if not self._match(TokenType.INDENT):
            # Tek satırlık blok olabilir
            stmt = self._parse_statement()
            if stmt:
                return [stmt]
            return []

        self._skip_newlines()

        while not self._is_at_end() and not self._check(TokenType.DEDENT):
            try:
                stmt = self._parse_statement()
                if stmt is not None:
                    body.append(stmt)
            except ParseError as e:
                self._errors.append(e)
                self._synchronize()
            self._skip_newlines()

        self._match(TokenType.DEDENT)
        return body

    # ─────────────────────────────────────────────────────
    # Üst Düzey Ayrıştırma
    # ─────────────────────────────────────────────────────

    def _parse_top_level(self) -> Optional[ASTNode]:
        """Üst düzey bir yapı ayrıştır."""
        self._skip_newlines()
        if self._is_at_end():
            return None

        decorators = []
        while self._match(TokenType.HASH):
            if self._previous().lexeme == "#":
                self._consume(TokenType.LEFT_BRACKET, "'[' bekleniyor")
            # Eğer lexeme "#[" ise zaten '[' yutulmuştur.
            decorator = self._consume(TokenType.IDENTIFIER, "Attribute adı bekleniyor").lexeme
            decorators.append(decorator)
            self._consume(TokenType.RIGHT_BRACKET, "']' bekleniyor")
            self._skip_newlines()

        if self._is_at_end():
            return None

        # ── module ──
        if self._check(TokenType.KW_MODULE):
            return self._parse_module()

        # ── add.code ──
        if self._check(TokenType.ADD_CODE):
            return self._parse_add_code()

        # ── use ──
        if self._check(TokenType.KW_USE):
            return self._parse_use()

        # ── pub ──
        if self._check(TokenType.KW_PUB):
            decl = self._parse_pub_declaration()
            if hasattr(decl, 'decorators'):
                decl.decorators.extend(decorators)
            return decl

        # ── hw_polymorph veya async ──
        is_hw_polymorph = False
        is_async = False
        if self._check(TokenType.KW_HW_POLYMORPH):
            is_hw_polymorph = True
            self._advance()
        if self._check(TokenType.KW_ASYNC):
            is_async = True
            self._advance()

        # ── Fonction.create veya fn ──
        if self._check(TokenType.FONCTION_CREATE, TokenType.KW_FN):
            decl = self._parse_function()
            decl.decorators.extend(decorators)
            decl.is_hw_polymorph = is_hw_polymorph
            decl.is_async = is_async
            return decl

        # ── struct / class / trait / impl / enum ──
        if self._check(TokenType.KW_STRUCT):
            decl = self._parse_struct()
            decl.decorators.extend(decorators)
            return decl
        if self._check(TokenType.KW_CLASS):
            return self._parse_class()
        if self._check(TokenType.KW_TRAIT):
            return self._parse_trait()
        if self._check(TokenType.KW_IMPL):
            return self._parse_impl()
        if self._check(TokenType.KW_ENUM):
            return self._parse_enum()

        # ── exploit / driver / hook ──
        if self._check(TokenType.KW_EXPLOIT):
            return self._parse_exploit()
        if self._check(TokenType.KW_DRIVER):
            return self._parse_driver()
        if self._check(TokenType.KW_HOOK):
            return self._parse_hook()

        # ── Genel deyim ──
        return self._parse_statement()

    # ─────────────────────────────────────────────────────
    # Bildirimler
    # ─────────────────────────────────────────────────────

    def _parse_module(self) -> ModuleDecl:
        loc = self._advance().location  # module
        name = self._consume(TokenType.IDENTIFIER, "Modül adı bekleniyor").lexeme
        return ModuleDecl(name=name, location=loc)

    def _parse_add_code(self) -> AddCodeDecl:
        """add.code "kütüphane" [as alias] [: import1, import2]"""
        loc = self._advance().location  # add.code
        lib_token = self._consume(TokenType.STRING, "Kütüphane adı (string) bekleniyor")
        lib_name = lib_token.value if lib_token.value else lib_token.lexeme.strip('"')

        alias = None
        imports = []

        if self._match(TokenType.KW_AS):
            alias = self._consume(TokenType.IDENTIFIER, "Alias adı bekleniyor").lexeme

        if self._match(TokenType.COLON):
            # Seçici import: add.code "os" : path, getcwd
            imports.append(self._consume(TokenType.IDENTIFIER, "Import adı bekleniyor").lexeme)
            while self._match(TokenType.COMMA):
                imports.append(self._consume(TokenType.IDENTIFIER, "Import adı bekleniyor").lexeme)

        return AddCodeDecl(library=lib_name, alias=alias, imports=imports, location=loc)

    def _parse_use(self) -> UseDecl:
        loc = self._advance().location  # use
        parts = [self._consume(TokenType.IDENTIFIER, "Modül yolu bekleniyor").lexeme]
        while self._match(TokenType.DOUBLE_COLON):
            parts.append(self._consume(TokenType.IDENTIFIER, "Modül parçası bekleniyor").lexeme)
        path = "::".join(parts)

        alias = None
        if self._match(TokenType.KW_AS):
            alias = self._consume(TokenType.IDENTIFIER, "Alias bekleniyor").lexeme

        return UseDecl(path=path, alias=alias, location=loc)

    def _parse_pub_declaration(self) -> ASTNode:
        """pub anahtar kelimesinden sonra gelen bildirimi ayrıştır."""
        self._advance()  # pub
        self._skip_newlines()

        if self._check(TokenType.FONCTION_CREATE, TokenType.KW_FN):
            fn = self._parse_function()
            fn.is_pub = True
            return fn
        elif self._check(TokenType.KW_STRUCT):
            s = self._parse_struct()
            s.is_pub = True
            return s
        elif self._check(TokenType.KW_CLASS):
            c = self._parse_class()
            c.is_pub = True
            return c
        elif self._check(TokenType.KW_TRAIT):
            t = self._parse_trait()
            t.is_pub = True
            return t
        elif self._check(TokenType.KW_EXPLOIT):
            return self._parse_exploit()
        elif self._check(TokenType.KW_DRIVER):
            return self._parse_driver()
        else:
            raise ParseError("pub'dan sonra bildirim bekleniyor", self._current())

    def _parse_function(self) -> FunctionDecl:
        """
        Fonction.create "isim" (param1: type, param2: type) -> ReturnType:
            body
        """
        loc = self._advance().location  # Fonction.create

        # Fonksiyon adı — string veya identifier olarak
        if self._check(TokenType.STRING):
            name_token = self._advance()
            name = name_token.value if name_token.value else name_token.lexeme.strip('"')
        else:
            name_token = self._consume(TokenType.IDENTIFIER, "Fonksiyon adı bekleniyor")
            name = name_token.lexeme

        # Parametreler
        params = []
        if self._match(TokenType.LEFT_PAREN):
            if not self._check(TokenType.RIGHT_PAREN):
                params = self._parse_param_list()
            self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")

        # Dönüş tipi
        return_type = None
        if self._match(TokenType.ARROW):
            return_type = self._parse_type_annotation()

        # : ile blok başı
        self._consume(TokenType.COLON, "':' bekleniyor (fonksiyon bloğu)")

        # Gövde
        body = self._parse_block()

        return FunctionDecl(
            name=name, params=params, return_type=return_type,
            body=body, location=loc
        )

    def _parse_param_list(self) -> List[Parameter]:
        """Fonksiyon parametrelerini ayrıştır."""
        params = []
        params.append(self._parse_parameter())
        while self._match(TokenType.COMMA):
            params.append(self._parse_parameter())
        return params

    def _parse_parameter(self) -> Parameter:
        is_mut = self._match(TokenType.KW_MUT)
        name = self._consume(TokenType.IDENTIFIER, "Parametre adı bekleniyor").lexeme
        type_ann = None
        default = None
        if self._match(TokenType.COLON):
            type_ann = self._parse_type_annotation()
        if self._match(TokenType.ASSIGN):
            default = self._parse_expression()
        return Parameter(name=name, type_annotation=type_ann,
                         default_value=default, is_mut=is_mut)

    def _parse_type_annotation(self) -> str:
        """Tip açıklaması ayrıştır (basit string olarak)."""
        parts = []
        tok = self._advance()
        parts.append(tok.lexeme)
        # Jenerik: Type<T> veya ptr<T>
        if self._match(TokenType.LESS):
            depth = 1
            while depth > 0 and not self._is_at_end():
                t = self._advance()
                parts.append(t.lexeme)
                if t.type == TokenType.LESS:
                    depth += 1
                elif t.type == TokenType.GREATER:
                    depth -= 1
        return "".join(parts)

    def _parse_struct(self) -> StructDecl:
        loc = self._advance().location  # struct
        name = self._consume(
            TokenType.TYPE_IDENT if self._check(TokenType.TYPE_IDENT) else TokenType.IDENTIFIER,
            "Struct adı bekleniyor"
        ).lexeme
        self._consume(TokenType.COLON, "':' bekleniyor")

        fields = []
        self._skip_newlines()
        if self._match(TokenType.INDENT):
            self._skip_newlines()
            while not self._is_at_end() and not self._check(TokenType.DEDENT):
                is_pub = self._match(TokenType.KW_PUB)
                fname = self._consume(TokenType.IDENTIFIER, "Alan adı bekleniyor").lexeme
                self._consume(TokenType.COLON, "':' bekleniyor")
                ftype = self._parse_type_annotation()
                fields.append(Parameter(name=fname, type_annotation=ftype, is_mut=is_pub))
                self._skip_newlines()
            self._match(TokenType.DEDENT)

        return StructDecl(name=name, fields=fields, location=loc)

    def _parse_class(self) -> ClassDecl:
        loc = self._advance().location  # class
        name = self._consume(
            TokenType.TYPE_IDENT if self._check(TokenType.TYPE_IDENT) else TokenType.IDENTIFIER,
            "Sınıf adı bekleniyor"
        ).lexeme

        bases = []
        if self._match(TokenType.LEFT_PAREN):
            if not self._check(TokenType.RIGHT_PAREN):
                bases.append(self._advance().lexeme)
                while self._match(TokenType.COMMA):
                    bases.append(self._advance().lexeme)
            self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")

        self._consume(TokenType.COLON, "':' bekleniyor")
        body = self._parse_block()
        return ClassDecl(name=name, base_classes=bases, body=body,
                         is_pub=False, location=loc)

    def _parse_trait(self) -> TraitDecl:
        loc = self._advance().location  # trait
        name = self._advance().lexeme
        self._consume(TokenType.COLON, "':' bekleniyor")
        methods = []
        self._skip_newlines()
        if self._match(TokenType.INDENT):
            self._skip_newlines()
            while not self._is_at_end() and not self._check(TokenType.DEDENT):
                if self._check(TokenType.FONCTION_CREATE, TokenType.KW_FN):
                    methods.append(self._parse_function())
                else:
                    self._advance()
                self._skip_newlines()
            self._match(TokenType.DEDENT)
        return TraitDecl(name=name, methods=methods, location=loc)

    def _parse_impl(self) -> ImplDecl:
        loc = self._advance().location  # impl
        type_name = self._advance().lexeme
        trait_name = None
        if self._match(TokenType.KW_FOR):
            trait_name = type_name
            type_name = self._advance().lexeme
        self._consume(TokenType.COLON, "':' bekleniyor")
        methods = []
        self._skip_newlines()
        if self._match(TokenType.INDENT):
            self._skip_newlines()
            while not self._is_at_end() and not self._check(TokenType.DEDENT):
                if self._check(TokenType.FONCTION_CREATE, TokenType.KW_FN):
                    methods.append(self._parse_function())
                elif self._check(TokenType.KW_PUB):
                    self._advance()
                    if self._check(TokenType.FONCTION_CREATE, TokenType.KW_FN):
                        fn = self._parse_function()
                        fn.is_pub = True
                        methods.append(fn)
                else:
                    self._advance()
                self._skip_newlines()
            self._match(TokenType.DEDENT)
        return ImplDecl(type_name=type_name, trait_name=trait_name,
                        methods=methods, location=loc)

    def _parse_exploit(self) -> ExploitDecl:
        loc = self._advance().location  # exploit
        name = self._advance().lexeme
        self._consume(TokenType.COLON, "':' bekleniyor")
        body = self._parse_block()
        return ExploitDecl(name=name, body=body, location=loc)

    def _parse_driver(self) -> DriverDecl:
        loc = self._advance().location  # driver
        name = self._advance().lexeme
        self._consume(TokenType.COLON, "':' bekleniyor")
        body = self._parse_block()
        return DriverDecl(name=name, body=body, location=loc)

    def _parse_hook(self) -> HookDecl:
        loc = self._advance().location  # hook
        target = self._advance().lexeme
        hook_type = "inline"
        if self._match(TokenType.LEFT_PAREN):
            while not self._check(TokenType.RIGHT_PAREN) and not self._is_at_end():
                if self._match(TokenType.IDENTIFIER) and self._previous().lexeme == "type":
                    self._match(TokenType.ASSIGN)
                    hook_type = self._advance().value or self._previous().lexeme.strip('"')
                else:
                    self._advance()
            self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")
        self._consume(TokenType.COLON, "':' bekleniyor")
        body = self._parse_block()
        return HookDecl(target=target, hook_type=hook_type, body=body, location=loc)

    # ─────────────────────────────────────────────────────
    # Deyimler (Statements)
    # ─────────────────────────────────────────────────────

    def _parse_statement(self) -> Optional[ASTNode]:
        """Bir deyim ayrıştır."""
        self._skip_newlines()
        if self._is_at_end():
            return None

        tok = self._current()

        is_temporal = False
        is_secure = False
        shared_target = None
        
        while tok.type in (TokenType.KW_TEMPORAL, TokenType.KW_SECURE, TokenType.KW_SHARED):
            if tok.type == TokenType.KW_TEMPORAL:
                is_temporal = True
                self._advance()
            elif tok.type == TokenType.KW_SECURE:
                is_secure = True
                self._advance()
            elif tok.type == TokenType.KW_SHARED:
                self._advance()
                if self._match(TokenType.LESS):
                    if self._check(TokenType.STRING):
                        target_tok = self._advance()
                        shared_target = target_tok.value or target_tok.lexeme.strip('"')
                    self._consume(TokenType.GREATER, "'>' bekleniyor (shared syntax)")
            tok = self._current()

        if tok.type in (TokenType.KW_LET, TokenType.KW_MUT, TokenType.KW_CONST):
            decl = self._parse_var_decl(
                mutable=(tok.type == TokenType.KW_MUT),
                const=(tok.type == TokenType.KW_CONST)
            )
            decl.is_temporal = is_temporal
            decl.is_secure = is_secure
            decl.shared_target = shared_target
            return decl
        if tok.type == TokenType.KW_IF:
            return self._parse_if()
        if tok.type == TokenType.KW_FOR:
            return self._parse_for()
        if tok.type == TokenType.KW_WHILE:
            return self._parse_while()
        if tok.type == TokenType.KW_LOOP:
            return self._parse_loop()
        if tok.type == TokenType.KW_MATCH:
            return self._parse_match()
        if tok.type == TokenType.KW_RETURN:
            return self._parse_return()
        if tok.type == TokenType.KW_BREAK:
            self._advance()
            return BreakStmt(location=tok.location)
        if tok.type == TokenType.KW_CONTINUE:
            self._advance()
            return ContinueStmt(location=tok.location)
        if tok.type == TokenType.KW_PASS:
            self._advance()
            return PassStmt(location=tok.location)
        if tok.type == TokenType.KW_UNSAFE:
            return self._parse_unsafe()
        if tok.type == TokenType.KW_KERNEL or tok.type == TokenType.KW_RING0:
            return self._parse_kernel_block()
        if tok.type in (TokenType.KW_PRINT, TokenType.KW_PRINTLN):
            return self._parse_print()
        if tok.type == TokenType.FONCTION_CREATE:
            return self._parse_function()
        if tok.type == TokenType.ADD_CODE:
            return self._parse_add_code()
        if tok.type == TokenType.KW_PUB:
            return self._parse_pub_declaration()
        if tok.type == TokenType.KW_ENUM:
            return self._parse_enum()

        # ── Yeni yapılar ──
        if tok.type == TokenType.KW_TRY:
            return self._parse_try_catch()
        if tok.type == TokenType.KW_THROW:
            return self._parse_throw()
        if tok.type == TokenType.KW_DELETE:
            return self._parse_delete()
        if tok.type == TokenType.KW_DO:
            return self._parse_do_while()
        if tok.type == TokenType.KW_DEFER:
            return self._parse_defer()

        if tok.type == TokenType.AT:
            loc = tok.location
            while self._check(TokenType.AT):
                self._advance()
            name = self._consume(TokenType.IDENTIFIER, "Değişken adı bekleniyor").lexeme
            self._consume(TokenType.ASSIGN, "'=' bekleniyor")
            val = self._parse_expression()
            return VarDecl(name=name, type_annotation=None, initializer=val, is_mutable=True, location=loc)

        # Genel ifade deyimi
        return self._parse_expression_statement()

    def _parse_var_decl(self, mutable: bool = False,
                        const: bool = False) -> VarDecl:
        loc = self._advance().location  # let / mut / const
        name = self._consume(TokenType.IDENTIFIER, "Değişken adı bekleniyor").lexeme
        type_ann = None
        init = None

        if self._match(TokenType.COLON):
            type_ann = self._parse_type_annotation()
        if self._match(TokenType.ASSIGN):
            init = self._parse_expression()

        return VarDecl(name=name, type_annotation=type_ann,
                       initializer=init, is_mutable=mutable,
                       is_const=const, location=loc)

    def _parse_if(self) -> IfStmt:
        loc = self._advance().location  # if
        condition = self._parse_expression()
        self._consume(TokenType.COLON, "':' bekleniyor (if bloğu)")
        then_body = self._parse_block()

        elif_clauses = []
        self._skip_newlines()
        while self._check(TokenType.KW_ELIF):
            self._advance()
            elif_cond = self._parse_expression()
            self._consume(TokenType.COLON, "':' bekleniyor (elif bloğu)")
            elif_body = self._parse_block()
            elif_clauses.append((elif_cond, elif_body))
            self._skip_newlines()

        else_body = []
        if self._match(TokenType.KW_ELSE):
            self._consume(TokenType.COLON, "':' bekleniyor (otherwise bloğu)")
            else_body = self._parse_block()

        return IfStmt(condition=condition, then_body=then_body,
                      elif_clauses=elif_clauses, else_body=else_body,
                      location=loc)

    def _parse_for(self) -> ForStmt:
        loc = self._advance().location  # for
        var = self._consume(TokenType.IDENTIFIER, "Döngü değişkeni bekleniyor").lexeme
        self._consume(TokenType.KW_IN, "'in' bekleniyor")
        iterable = self._parse_expression()
        self._consume(TokenType.COLON, "':' bekleniyor (for bloğu)")
        body = self._parse_block()
        return ForStmt(variable=var, iterable=iterable, body=body, location=loc)

    def _parse_while(self) -> WhileStmt:
        loc = self._advance().location  # while
        condition = self._parse_expression()
        self._consume(TokenType.COLON, "':' bekleniyor (return.code bloğu)")
        body = self._parse_block()
        return WhileStmt(condition=condition, body=body, location=loc)

    def _parse_loop(self) -> LoopStmt:
        loc = self._advance().location  # loop
        self._consume(TokenType.COLON, "':' bekleniyor (loop bloğu)")
        body = self._parse_block()
        return LoopStmt(body=body, location=loc)

    def _parse_match(self) -> MatchStmt:
        loc = self._advance().location  # match
        value = self._parse_expression()
        self._consume(TokenType.COLON, "':' bekleniyor (match bloğu)")

        arms = []
        self._skip_newlines()
        if self._match(TokenType.INDENT):
            self._skip_newlines()
            while not self._is_at_end() and not self._check(TokenType.DEDENT):
                pattern = self._parse_expression()
                self._consume(TokenType.FAT_ARROW, "'=>' bekleniyor")
                arm_body = self._parse_expression()
                arms.append((pattern, arm_body))
                self._skip_newlines()
            self._match(TokenType.DEDENT)

        return MatchStmt(value=value, arms=arms, location=loc)

    def _parse_return(self) -> ReturnStmt:
        loc = self._advance().location  # return
        value = None
        if not self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            value = self._parse_expression()
        return ReturnStmt(value=value, location=loc)

    def _parse_unsafe(self) -> UnsafeBlock:
        loc = self._advance().location  # unsafe
        self._consume(TokenType.COLON, "':' bekleniyor (unsafe bloğu)")
        body = self._parse_block()
        return UnsafeBlock(body=body, location=loc)

    def _parse_kernel_block(self) -> KernelBlock:
        loc = self._advance().location  # kernel / ring0
        self._consume(TokenType.COLON, "':' bekleniyor (kernel bloğu)")
        body = self._parse_block()
        return KernelBlock(body=body, location=loc)

    def _parse_print(self) -> PrintStmt:
        tok = self._advance()
        newline = tok.type == TokenType.KW_PRINTLN
        value = None
        if not self._check(TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            value = self._parse_expression()
        return PrintStmt(value=value, newline=newline, location=tok.location)

    def _parse_expression_statement(self) -> ASTNode:
        loc = self._current().location
        expr = self._parse_expression()

        # Atama kontrolü: x = value (tüm atama operatörleri)
        if self._check(TokenType.ASSIGN, TokenType.PLUS_ASSIGN, TokenType.MINUS_ASSIGN,
                       TokenType.STAR_ASSIGN, TokenType.SLASH_ASSIGN,
                       TokenType.PERCENT_ASSIGN, TokenType.AMP_ASSIGN,
                       TokenType.PIPE_ASSIGN, TokenType.CARET_ASSIGN,
                       TokenType.SHIFT_LEFT_ASSIGN, TokenType.SHIFT_RIGHT_ASSIGN,
                       TokenType.DOUBLE_STAR_ASSIGN):
            op = self._advance().lexeme
            value = self._parse_expression()
            
            # Kural: a = integer(...) yasak, doğrusu @a = integer(...)
            if op == "=" and isinstance(value, CallExpr) and isinstance(value.callee, IdentifierExpr) and value.callee.name == "integer":
                raise ParseError("integer() çağrısı için @değişken = integer(...) formatını kullanmalısınız.", self._previous())
                
            return ExpressionStmt(
                expression=AssignExpr(target=expr, operator=op, value=value, location=loc),
                location=loc
            )

        return ExpressionStmt(expression=expr, location=loc)

    # ─────────────────────────────────────────────────────
    # Yeni Yapıların Ayrıştırıcıları
    # ─────────────────────────────────────────────────────

    def _parse_try_catch(self) -> TryCatchStmt:
        """try: ... catch err: ... finally: ..."""
        loc = self._advance().location  # try
        self._consume(TokenType.COLON, "':' bekleniyor (try bloğu)")
        try_body = self._parse_block()

        catch_var = None
        catch_body = []
        finally_body = []

        self._skip_newlines()
        if self._match(TokenType.KW_CATCH):
            if self._check(TokenType.IDENTIFIER):
                catch_var = self._advance().lexeme
            self._consume(TokenType.COLON, "':' bekleniyor (catch bloğu)")
            catch_body = self._parse_block()

        self._skip_newlines()
        if self._match(TokenType.KW_FINALLY):
            self._consume(TokenType.COLON, "':' bekleniyor (finally bloğu)")
            finally_body = self._parse_block()

        return TryCatchStmt(
            try_body=try_body, catch_var=catch_var,
            catch_body=catch_body, finally_body=finally_body,
            location=loc
        )

    def _parse_throw(self) -> ThrowStmt:
        loc = self._advance().location  # throw
        value = self._parse_expression()
        return ThrowStmt(value=value, location=loc)

    def _parse_enum(self) -> EnumDecl:
        """enum Color: RED, GREEN = 1, BLUE"""
        loc = self._advance().location  # enum
        name = self._consume(
            TokenType.TYPE_IDENT if self._check(TokenType.TYPE_IDENT) else TokenType.IDENTIFIER,
            "Enum adı bekleniyor"
        ).lexeme
        self._consume(TokenType.COLON, "':' bekleniyor (enum bloğu)")

        variants = []
        self._skip_newlines()
        if self._match(TokenType.INDENT):
            self._skip_newlines()
            auto_value = 0
            while not self._is_at_end() and not self._check(TokenType.DEDENT):
                vname = self._consume(TokenType.IDENTIFIER, "Variant adı bekleniyor").lexeme
                if self._match(TokenType.ASSIGN):
                    val_expr = self._parse_expression()
                    if isinstance(val_expr, LiteralExpr):
                        auto_value = val_expr.value
                    variants.append((vname, val_expr))
                else:
                    variants.append((vname, LiteralExpr(value=auto_value, literal_type="int", location=self._current().location)))
                auto_value = (auto_value + 1) if isinstance(auto_value, int) else auto_value
                self._match(TokenType.COMMA)
                self._skip_newlines()
            self._match(TokenType.DEDENT)
        else:
            # Tek satırlık: enum Color: RED, GREEN, BLUE
            auto_value = 0
            vname = self._consume(TokenType.IDENTIFIER, "Variant adı bekleniyor").lexeme
            variants.append((vname, LiteralExpr(value=auto_value, literal_type="int", location=self._current().location)))
            auto_value += 1
            while self._match(TokenType.COMMA):
                vname = self._consume(TokenType.IDENTIFIER, "Variant adı bekleniyor").lexeme
                variants.append((vname, LiteralExpr(value=auto_value, literal_type="int", location=self._current().location)))
                auto_value += 1

        return EnumDecl(name=name, variants=variants, location=loc)

    def _parse_delete(self) -> DeleteStmt:
        loc = self._advance().location  # delete
        target = self._parse_expression()
        return DeleteStmt(target=target, location=loc)

    def _parse_do_while(self) -> DoWhileStmt:
        """do: body return.code condition"""
        loc = self._advance().location  # do
        self._consume(TokenType.COLON, "':' bekleniyor (do bloğu)")
        body = self._parse_block()
        self._skip_newlines()
        self._consume(TokenType.KW_WHILE, "'return.code' bekleniyor (do-while koşulu)")
        condition = self._parse_expression()
        return DoWhileStmt(body=body, condition=condition, location=loc)

    def _parse_defer(self) -> DeferStmt:
        loc = self._advance().location  # defer
        self._consume(TokenType.COLON, "':' bekleniyor (defer bloğu)")
        body = self._parse_block()
        return DeferStmt(body=body, location=loc)

    # ─────────────────────────────────────────────────────
    # İfadeler (Expressions) — Precedence Climbing
    # ─────────────────────────────────────────────────────

    def _parse_expression(self) -> ASTNode:
        return self._parse_pipe()

    def _parse_pipe(self) -> ASTNode:
        """Pipe operatörü: value |> fn1 |> fn2"""
        expr = self._parse_ternary()
        while self._match(TokenType.PIPE_OPERATOR):
            func = self._parse_ternary()
            expr = PipeExpr(value=expr, function=func, location=expr.location)
        return expr

    def _parse_ternary(self) -> ASTNode:
        """Ternary: condition ? true_val : false_val"""
        expr = self._parse_null_coalesce()
        if self._match(TokenType.QUESTION):
            true_val = self._parse_expression()
            self._consume(TokenType.COLON, "':' bekleniyor (ternary ifadesi)")
            false_val = self._parse_expression()
            expr = TernaryExpr(condition=expr, true_value=true_val,
                               false_value=false_val, location=expr.location)
        return expr

    def _parse_null_coalesce(self) -> ASTNode:
        """Null coalescing: value ?? default"""
        left = self._parse_or()
        while self._match(TokenType.NULL_COALESCE):
            right = self._parse_or()
            left = BinaryExpr(left=left, operator="??", right=right,
                              location=left.location)
        return left

    def _parse_or(self) -> ASTNode:
        left = self._parse_and()
        while self._match(TokenType.LOGICAL_OR, TokenType.KW_OR):
            op = self._previous().lexeme
            right = self._parse_and()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_and(self) -> ASTNode:
        left = self._parse_equality()
        while self._match(TokenType.LOGICAL_AND, TokenType.KW_AND):
            op = self._previous().lexeme
            right = self._parse_equality()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_equality(self) -> ASTNode:
        left = self._parse_comparison()
        while self._match(TokenType.EQUAL, TokenType.NOT_EQUAL):
            op = self._previous().lexeme
            right = self._parse_comparison()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_comparison(self) -> ASTNode:
        left = self._parse_bitwise_or()
        while self._match(TokenType.LESS, TokenType.GREATER,
                          TokenType.LESS_EQUAL, TokenType.GREATER_EQUAL,
                          TokenType.KW_IS, TokenType.KW_IN):
            op = self._previous().lexeme
            right = self._parse_bitwise_or()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_bitwise_or(self) -> ASTNode:
        left = self._parse_bitwise_xor()
        while self._match(TokenType.PIPE):
            right = self._parse_bitwise_xor()
            left = BinaryExpr(left=left, operator="|", right=right,
                              location=left.location)
        return left

    def _parse_bitwise_xor(self) -> ASTNode:
        left = self._parse_bitwise_and()
        while self._match(TokenType.CARET):
            right = self._parse_bitwise_and()
            left = BinaryExpr(left=left, operator="^", right=right,
                              location=left.location)
        return left

    def _parse_bitwise_and(self) -> ASTNode:
        left = self._parse_shift()
        while self._match(TokenType.AMPERSAND):
            right = self._parse_shift()
            left = BinaryExpr(left=left, operator="&", right=right,
                              location=left.location)
        return left

    def _parse_shift(self) -> ASTNode:
        left = self._parse_addition()
        while self._match(TokenType.SHIFT_LEFT, TokenType.SHIFT_RIGHT):
            op = self._previous().lexeme
            right = self._parse_addition()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_addition(self) -> ASTNode:
        left = self._parse_multiplication()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous().lexeme
            right = self._parse_multiplication()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_multiplication(self) -> ASTNode:
        left = self._parse_power()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._previous().lexeme
            right = self._parse_power()
            left = BinaryExpr(left=left, operator=op, right=right,
                              location=left.location)
        return left

    def _parse_power(self) -> ASTNode:
        left = self._parse_unary()
        if self._match(TokenType.DOUBLE_STAR):
            right = self._parse_power()  # Sağdan birleşimli
            left = BinaryExpr(left=left, operator="**", right=right,
                              location=left.location)
        return left

    def _parse_unary(self) -> ASTNode:
        if self._match(TokenType.KW_AWAIT):
            expr = self._parse_unary()
            return AwaitExpr(expression=expr, location=self._previous().location)
        if self._match(TokenType.MINUS, TokenType.BANG, TokenType.TILDE, TokenType.KW_NOT):
            op = self._previous().lexeme
            operand = self._parse_unary()
            return UnaryExpr(operator=op, operand=operand,
                             location=self._previous().location)
        return self._parse_postfix()

    def _parse_postfix(self) -> ASTNode:
        expr = self._parse_primary()

        while True:
            if self._match(TokenType.LEFT_PAREN):
                # Fonksiyon çağrısı
                args = []
                if not self._check(TokenType.RIGHT_PAREN):
                    args.append(self._parse_expression())
                    while self._match(TokenType.COMMA):
                        args.append(self._parse_expression())
                self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")
                expr = CallExpr(callee=expr, arguments=args,
                                location=expr.location)
            elif self._match(TokenType.DOT):
                member = self._consume(TokenType.IDENTIFIER, "Üye adı bekleniyor").lexeme
                expr = MemberAccessExpr(object=expr, member=member,
                                        location=expr.location)
            elif self._match(TokenType.DOUBLE_COLON):
                member = self._advance().lexeme
                expr = MemberAccessExpr(object=expr, member=member,
                                        is_static=True, location=expr.location)
            elif self._match(TokenType.LEFT_BRACKET):
                index = self._parse_expression()
                self._consume(TokenType.RIGHT_BRACKET, "']' bekleniyor")
                expr = IndexExpr(object=expr, index=index,
                                 location=expr.location)
            elif self._match(TokenType.KW_AS):
                target = self._parse_type_annotation()
                expr = CastExpr(operand=expr, target_type=target,
                                location=expr.location)
            elif self._match(TokenType.DOT_DOT):
                inclusive = self._match(TokenType.ASSIGN)  # ..=
                end = self._parse_addition()
                expr = RangeExpr(start=expr, end=end, inclusive=inclusive,
                                 location=expr.location)
            else:
                break

        return expr

    def _parse_primary(self) -> ASTNode:
        tok = self._current()

        # Literaller
        if self._match(TokenType.INTEGER, TokenType.HEX_INTEGER,
                       TokenType.BINARY_INT, TokenType.OCTAL_INT):
            return LiteralExpr(value=tok.value, literal_type="int",
                               location=tok.location)

        if self._match(TokenType.FLOAT):
            return LiteralExpr(value=tok.value, literal_type="float",
                               location=tok.location)

        if self._match(TokenType.STRING, TokenType.RAW_STRING, TokenType.FSTRING):
            return LiteralExpr(value=tok.value, literal_type="string",
                               location=tok.location)

        if self._match(TokenType.BYTE_STRING):
            return LiteralExpr(value=tok.value, literal_type="bytes",
                               location=tok.location)

        if self._match(TokenType.CHAR):
            return LiteralExpr(value=tok.value, literal_type="char",
                               location=tok.location)

        if self._match(TokenType.BOOL_TRUE):
            return LiteralExpr(value=True, literal_type="bool",
                               location=tok.location)

        if self._match(TokenType.BOOL_FALSE):
            return LiteralExpr(value=False, literal_type="bool",
                               location=tok.location)

        if self._match(TokenType.NULL):
            return LiteralExpr(value=None, literal_type="null",
                               location=tok.location)

        # Tanımlayıcı
        if self._match(TokenType.IDENTIFIER, TokenType.TYPE_IDENT, TokenType.KW_INPUT):
            return IdentifierExpr(name=tok.lexeme, location=tok.location)

        # volatile prefix: no-op wrapper for unsafe pointer access
        if self._match(TokenType.KW_VOLATILE):
            return self._parse_primary()

        # drop/alloc as built-in identifiers
        if self._match(TokenType.KW_DROP):
            return IdentifierExpr(name="drop", location=tok.location)
        if self._match(TokenType.KW_ALLOC):
            return IdentifierExpr(name="alloc", location=tok.location)
        if self._match(TokenType.KW_PTR):
            return IdentifierExpr(name="ptr", location=tok.location)

        if self._match(TokenType.KW_ASM):
            return self._parse_asm_expr()

        if self._match(TokenType.KW_SHELLCODE):
            return self._parse_shellcode_expr()

        # self
        if self._match(TokenType.KW_SELF):
            return IdentifierExpr(name="self", location=tok.location)

        # Gruplandırma veya tuple literali: (expr) veya (a, b, c)
        if self._match(TokenType.LEFT_PAREN):
            if self._check(TokenType.RIGHT_PAREN):
                self._advance()
                return TupleExpr(elements=[], location=tok.location)

            expr = self._parse_expression()
            if self._match(TokenType.COMMA):
                elements = [expr]
                while not self._check(TokenType.RIGHT_PAREN) and not self._is_at_end():
                    elements.append(self._parse_expression())
                    self._match(TokenType.COMMA)
                self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")
                return TupleExpr(elements=elements, location=tok.location)

            self._consume(TokenType.RIGHT_PAREN, "')' bekleniyor")
            return expr

        # Dict / Sözlük: {key: value, ...}
        if self._match(TokenType.LEFT_BRACE):
            return self._parse_dict_or_block(tok.location)

        # Liste: [a, b, c]
        if self._match(TokenType.LEFT_BRACKET):
            elements = []
            if not self._check(TokenType.RIGHT_BRACKET):
                elements.append(self._parse_expression())
                while self._match(TokenType.COMMA):
                    if self._check(TokenType.RIGHT_BRACKET):
                        break
                    elements.append(self._parse_expression())
            self._consume(TokenType.RIGHT_BRACKET, "']' bekleniyor")
            return ListExpr(elements=elements, location=tok.location)

        # Lambda: |x, y| => x + y
        if self._match(TokenType.PIPE):
            return self._parse_lambda(tok.location)

        # Underscore (match wildcard)
        if self._check(TokenType.IDENTIFIER) and self._current().lexeme == "_":
            self._advance()
            return IdentifierExpr(name="_", location=tok.location)

        raise ParseError(f"Beklenmeyen token: {tok.lexeme!r} ({tok.type.name})",
                         tok)

    def _parse_dict_or_block(self, loc: SourceLocation) -> ASTNode:
        """Dict literal: {key: value, ...} veya boş dict: {}"""
        pairs = []
        if self._check(TokenType.RIGHT_BRACE):
            self._advance()
            return DictExpr(pairs=pairs, location=loc)

        # İlk elemanı ayrıştır
        key = self._parse_expression()
        if self._match(TokenType.COLON):
            # Bu bir dict
            value = self._parse_expression()
            pairs.append((key, value))
            while self._match(TokenType.COMMA):
                if self._check(TokenType.RIGHT_BRACE):
                    break
                k = self._parse_expression()
                self._consume(TokenType.COLON, "':' bekleniyor (dict çifti)")
                v = self._parse_expression()
                pairs.append((k, v))
            self._consume(TokenType.RIGHT_BRACE, "'}' bekleniyor")
            return DictExpr(pairs=pairs, location=loc)
        else:
            # Tek elemanlı dict değil — hata
            self._consume(TokenType.RIGHT_BRACE, "'}' bekleniyor")
            return DictExpr(pairs=[], location=loc)

    def _collect_brace_block_text(self) -> str:
        parts = []
        depth = 1
        while not self._is_at_end() and depth > 0:
            tok = self._advance()
            if tok.type == TokenType.LEFT_BRACE:
                depth += 1
            elif tok.type == TokenType.RIGHT_BRACE:
                depth -= 1
                if depth == 0:
                    break
            if depth > 0:
                parts.append(tok.lexeme)
                parts.append(" ")
        return "".join(parts).strip()

    def _parse_asm_expr(self) -> AsmExpr:
        loc = self._previous().location
        self._consume(TokenType.LEFT_BRACE, "'{' bekleniyor (asm bloğu)")
        code = self._collect_brace_block_text()
        return AsmExpr(code=code, location=loc)

    def _parse_shellcode_expr(self) -> ShellcodeExpr:
        loc = self._previous().location
        arch = "x86_64"
        if self._check(TokenType.IDENTIFIER, TokenType.TYPE_IDENT):
            arch = self._advance().lexeme
        self._consume(TokenType.LEFT_BRACE, "'{' bekleniyor (shellcode bloğu)")
        code = self._collect_brace_block_text()
        return ShellcodeExpr(arch=arch, code=code, location=loc)

    def _parse_lambda(self, loc: SourceLocation) -> LambdaExpr:
        """|x, y| => x + y"""
        params = []
        if not self._check(TokenType.PIPE):
            params.append(self._parse_parameter())
            while self._match(TokenType.COMMA):
                params.append(self._parse_parameter())
        self._consume(TokenType.PIPE, "'|' bekleniyor (lambda kapanış)")
        self._consume(TokenType.FAT_ARROW, "'=>' bekleniyor (lambda gövdesi)")
        body = self._parse_expression()
        return LambdaExpr(params=params, body=body, location=loc)
