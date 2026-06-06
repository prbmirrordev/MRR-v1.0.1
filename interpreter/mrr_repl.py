"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR REPL — İnteraktif Terminal (Read-Eval-Print-Loop)          ║
║                                                                  ║
║  Python'un interaktif terminali gibi, MRR dilinin kendine ait   ║
║  bir komut satırı ortamı.                                        ║
║                                                                  ║
║  Özellikler:                                                    ║
║    - Renkli prompt ve çıktılar                                  ║
║    - Çok satırlı giriş desteği                                  ║
║    - Komut geçmişi (ok tuşları)                                 ║
║    - Otomatik sonuç gösterimi                                    ║
║    - Özel dot-komutlar (.help, .vars, .fns, .clear, vb.)       ║
║    - Hata yakalama (program çökmez)                              ║
║    - Tab-completion                                              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import time
import traceback
from typing import Optional, List

from interpreter.mrr_lexer import Lexer, LexerError
from interpreter.mrr_parser import Parser, ParseError
from interpreter.mrr_evaluator import Evaluator, MRRFunction, MRRStruct, MRRInstance, MRRRuntimeError
from interpreter.mrr_ffi import FFIBridge, SandboxPolicy
from interpreter.mrr_locale import ask_yes_no, translate
from interpreter.mrr_autocorrect import autocorrect_source


# ═══════════════════════════════════════════════════════════
# ─── ANSI RENK KODLARI ───────────────────────────────────
# ═══════════════════════════════════════════════════════════

class Colors:
    """Terminal renk kodları."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"

    # Ön plan renkleri
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    WHITE = "\033[97m"
    GRAY = "\033[90m"

    # Arka plan
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE = "\033[44m"

    @staticmethod
    def supports_color() -> bool:
        """Terminal renk desteği var mı?"""
        if os.name == 'nt':
            # Windows 10+ ANSI desteği
            os.system("")  # ANSI escape sequence desteğini etkinleştir
            return True
        return hasattr(sys.stdout, 'isatty') and sys.stdout.isatty()


# ═══════════════════════════════════════════════════════════
# ─── MRR REPL ─────────────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class MRRREPL:
    """
    MRR İnteraktif Terminal — Read-Eval-Print-Loop.

    Python'un `>>>` promptu gibi, MRR'ın `mrr>` promptu ile
    anlık kod çalıştırma ortamı sunar.
    """

    VERSION = "0.3.0"
    PROMPT = "mrr> "
    CONTINUATION_PROMPT = "...> "

    # Blok başlatan anahtar kelimeler/tokenlar
    BLOCK_STARTERS = {
        ":", "Fonction.create", "Function.create", "fn", "if", "elif",
        "otherwise", "for", "loop", "match", "struct", "class", "trait",
        "impl", "exploit", "driver", "hook", "unsafe", "kernel", "ring0",
        "try", "catch", "finally", "do", "defer", "enum", "return.code"
    }

    def __init__(self):
        self.use_color = Colors.supports_color()
        self.evaluator = Evaluator()
        self.history: List[str] = []
        self.running = True
        self.exec_count = 0

        # FFI bridge kurulumu
        sandbox_policy = SandboxPolicy(
            max_memory_mb=256,
            timeout_seconds=30,
            allow_network=True,
            allow_filesystem=True
        )
        self.ffi_bridge = FFIBridge(policy=sandbox_policy)
        self.evaluator.ffi_bridge = self.ffi_bridge

        # readline desteği (komut geçmişi + tab completion)
        self._setup_readline()

    def _setup_readline(self) -> None:
        """readline modülünü yapılandır (eğer mevcutsa)."""
        try:
            import readline
            readline.set_completer(self._completer)
            readline.parse_and_bind("tab: complete")
            # Windows'ta pyreadline3 gerekebilir
        except ImportError:
            pass  # readline yoksa sessizce devam et

    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab-completion için tamamlama fonksiyonu."""
        completions = []

        # Anahtar kelimeler
        keywords = [
            "let", "mut", "const", "if", "elif", "otherwise", "for", "in",
            "return.code", "loop", "break", "continue", "match", "return",
            "Fonction.create", "Function.create", "fn", "struct", "class",
            "trait", "impl", "pub", "priv", "module", "use", "add.code",
            "unsafe", "kernel", "ring0", "exploit", "hook", "driver",
            "print", "println", "input", "true", "false", "null", "self",
            "try", "catch", "finally", "throw", "delete", "do", "defer",
            "enum", "pass", "as", "is", "not", "and", "or", "async", "await",
        ]

        # Yerleşik fonksiyonlar
        builtins = [
            "print", "println", "input", "integer", "float", "str", "bool",
            "byte", "len", "range", "append", "pop", "abs", "min", "max",
            "typeof", "sizeof", "exit", "time", "hex", "bin", "oct",
            "split", "join", "replace", "upper", "lower", "trim",
            "contains", "starts_with", "ends_with", "format", "chr", "ord",
            "reverse", "sort", "map", "filter", "reduce", "enumerate", "zip",
            "keys", "values", "items", "has_key", "insert", "remove", "slice",
            "flat", "round", "pow", "sqrt", "sleep", "random_int", "assert",
            "type_name", "hash", "id", "readfile", "writefile",
        ]

        # Dot komutlar
        dot_commands = [
            ".help", ".clear", ".vars", ".fns", ".load", ".time",
            ".ast", ".tokens", ".reset", ".exit", ".quit", ".version",
        ]

        # Tanımlı değişkenler
        user_vars = list(self.evaluator.global_env._vars.keys())

        all_options = keywords + builtins + dot_commands + user_vars

        for option in all_options:
            if option.startswith(text):
                completions.append(option)

        if state < len(completions):
            return completions[state]
        return None

    # ─────────────────────────────────────────────────────
    # Renklendirme Yardımcıları
    # ─────────────────────────────────────────────────────

    def _c(self, text: str, color: str) -> str:
        """Metni renklendir."""
        if self.use_color:
            return f"{color}{text}{Colors.RESET}"
        return text

    def _prompt(self) -> str:
        """Renkli prompt."""
        return self._c(self.PROMPT, Colors.CYAN + Colors.BOLD)

    def _cont_prompt(self) -> str:
        """Continuation prompt."""
        return self._c(self.CONTINUATION_PROMPT, Colors.GRAY)

    # ─────────────────────────────────────────────────────
    # Banner
    # ─────────────────────────────────────────────────────

    def _print_banner(self) -> None:
        """Başlangıç ekranı."""
        banner = f"""
{self._c("╔══════════════════════════════════════════════════════════════╗", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("███╗   ███╗ ██████╗  ██████╗", Colors.RED + Colors.BOLD)}                                {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("████╗ ████║ ██╔══██╗ ██╔══██╗", Colors.RED + Colors.BOLD)}                               {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("██╔████╔██║ ██████╔╝ ██████╔╝", Colors.RED + Colors.BOLD)}                               {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("██║╚██╔╝██║ ██╔══██╗ ██╔══██╗", Colors.RED + Colors.BOLD)}                               {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("██║ ╚═╝ ██║ ██║  ██║ ██║  ██║", Colors.RED + Colors.BOLD)}                               {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("╚═╝     ╚═╝ ╚═╝  ╚═╝ ╚═╝  ╚═╝", Colors.RED + Colors.BOLD)}                               {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}                                                              {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("Memory, Registers, Rings", Colors.YELLOW)}  {self._c(f"v{self.VERSION}", Colors.GREEN)}                        {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("Siber Güvenlik Odaklı Sistem Programlama Dili", Colors.GRAY)}             {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}                                                              {self._c("║", Colors.CYAN)}
{self._c("║", Colors.CYAN)}  {self._c("Yardım:", Colors.WHITE)} {self._c(".help", Colors.GREEN)}   {self._c("Çıkış:", Colors.WHITE)} {self._c(".exit", Colors.GREEN)}   {self._c("Temizle:", Colors.WHITE)} {self._c(".clear", Colors.GREEN)}            {self._c("║", Colors.CYAN)}
{self._c("╚══════════════════════════════════════════════════════════════╝", Colors.CYAN)}
"""
        print(banner)

    # ─────────────────────────────────────────────────────
    # Dot Komutları
    # ─────────────────────────────────────────────────────

    def _handle_dot_command(self, cmd: str) -> bool:
        """Dot komutunu işle. True döndürürse normal işleme atlanır."""
        parts = cmd.strip().split(None, 1)
        command = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        match command:
            case ".help":
                self._cmd_help()
            case ".clear" | ".cls":
                os.system("cls" if os.name == "nt" else "clear")
            case ".vars":
                self._cmd_vars()
            case ".fns":
                self._cmd_fns()
            case ".load":
                self._cmd_load(arg)
            case ".time":
                self._cmd_time(arg)
            case ".ast":
                self._cmd_ast(arg)
            case ".tokens":
                self._cmd_tokens(arg)
            case ".reset":
                self._cmd_reset()
            case ".exit" | ".quit":
                self.running = False
                print(self._c("\n👋 MRR Terminali kapatılıyor...", Colors.YELLOW))
            case ".version":
                print(self._c(f"MRR v{self.VERSION}", Colors.GREEN))
            case _:
                print(self._c(f"❌ Bilinmeyen komut: {command}", Colors.RED))
                print(self._c("   .help yazarak kullanılabilir komutları görün.", Colors.GRAY))

        return True

    def _cmd_help(self) -> None:
        """Yardım göster."""
        help_text = f"""
{self._c("═══ MRR REPL Yardım ═══", Colors.CYAN + Colors.BOLD)}

{self._c("Genel Kullanım:", Colors.YELLOW + Colors.BOLD)}
  Kod yazın ve Enter'a basın. Sonuç otomatik gösterilir.
  Blok yapıları (if, for, fn, vb.) sonunda ':' koyun,
  devam satırlarını yazın, boş satır ile bloğu bitirin.

{self._c("Dot Komutları:", Colors.YELLOW + Colors.BOLD)}
  {self._c(".help", Colors.GREEN)}              Bu yardım metnini gösterir
  {self._c(".clear", Colors.GREEN)}             Ekranı temizler
  {self._c(".vars", Colors.GREEN)}              Tanımlı değişkenleri listeler
  {self._c(".fns", Colors.GREEN)}               Tanımlı fonksiyonları listeler
  {self._c(".load <dosya>", Colors.GREEN)}      Bir .mrr dosyasını yükler ve çalıştırır
  {self._c(".time <ifade>", Colors.GREEN)}      İfadenin çalışma süresini ölçer
  {self._c(".ast <ifade>", Colors.GREEN)}       İfadenin AST yapısını gösterir
  {self._c(".tokens <ifade>", Colors.GREEN)}    İfadenin token akışını gösterir
  {self._c(".reset", Colors.GREEN)}             Ortamı sıfırlar (tüm değişkenleri siler)
  {self._c(".version", Colors.GREEN)}           Versiyon bilgisini gösterir
  {self._c(".exit / .quit", Colors.GREEN)}      REPL'den çıkar

{self._c("Kısayollar:", Colors.YELLOW + Colors.BOLD)}
  {self._c("Ctrl+C", Colors.GREEN)}             Çalışan kodu iptal eder
  {self._c("Ctrl+D", Colors.GREEN)}             REPL'den çıkar
  {self._c("Tab", Colors.GREEN)}                Otomatik tamamlama
  {self._c("↑ / ↓", Colors.GREEN)}             Komut geçmişinde gezinme

{self._c("Örnekler:", Colors.YELLOW + Colors.BOLD)}
  {self._c('let x = 42', Colors.WHITE)}
  {self._c('println "Merhaba MRR!"', Colors.WHITE)}
  {self._c('Fonction.create "topla" (a, b):', Colors.WHITE)}
  {self._c('    return a + b', Colors.WHITE)}
  {self._c('', Colors.WHITE)}
  {self._c('topla(3, 5)', Colors.WHITE)}
"""
        print(help_text)

    def _cmd_vars(self) -> None:
        """Tanımlı değişkenleri listele."""
        env = self.evaluator.global_env
        user_vars = {}
        for name, value in env._vars.items():
            if not isinstance(value, MRRFunction):
                user_vars[name] = value

        if not user_vars:
            print(self._c("  (Tanımlı değişken yok)", Colors.GRAY))
            return

        print(self._c("═══ Tanımlı Değişkenler ═══", Colors.CYAN))
        for name, value in user_vars.items():
            mut_flag = self._c("mut", Colors.YELLOW) if name in env._mutables else self._c("let", Colors.BLUE)
            formatted = self.evaluator._format_value(value)
            type_name = self.evaluator._builtin_type_name([value])
            print(f"  {mut_flag} {self._c(name, Colors.WHITE + Colors.BOLD)} : "
                  f"{self._c(type_name, Colors.MAGENTA)} = {self._c(formatted, Colors.GREEN)}")

    def _cmd_fns(self) -> None:
        """Tanımlı fonksiyonları listele."""
        env = self.evaluator.global_env
        user_fns = {}
        builtin_fns = {}
        for name, value in env._vars.items():
            if isinstance(value, MRRFunction):
                if value.is_builtin:
                    builtin_fns[name] = value
                else:
                    user_fns[name] = value

        if user_fns:
            print(self._c("═══ Kullanıcı Fonksiyonları ═══", Colors.CYAN))
            for name, fn in user_fns.items():
                params = ", ".join(p.name for p in fn.params)
                ret = f" -> {fn.return_type}" if fn.return_type else ""
                print(f"  {self._c('fn', Colors.BLUE)} {self._c(name, Colors.WHITE + Colors.BOLD)}"
                      f"({self._c(params, Colors.YELLOW)}){self._c(ret, Colors.MAGENTA)}")
        else:
            print(self._c("  (Kullanıcı tanımlı fonksiyon yok)", Colors.GRAY))

        print(self._c(f"\n  + {len(builtin_fns)} yerleşik fonksiyon", Colors.GRAY))

    def _cmd_load(self, filepath: str) -> None:
        """Dosya yükle ve çalıştır."""
        if not filepath:
            print(self._c("❌ Kullanım: .load <dosya.mrr>", Colors.RED))
            return

        filepath = filepath.strip().strip('"').strip("'")
        if not os.path.exists(filepath):
            print(self._c(f"❌ Dosya bulunamadı: {filepath}", Colors.RED))
            return

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()

            print(self._c(f"📂 Yükleniyor: {filepath}", Colors.CYAN))
            self._execute_source(source, filepath)
            print(self._c(f"✅ {filepath} başarıyla yüklendi.", Colors.GREEN))
        except Exception as e:
            print(self._c(f"❌ Yükleme hatası: {e}", Colors.RED))

    def _cmd_time(self, code: str) -> None:
        """Kodun çalışma süresini ölç."""
        if not code:
            print(self._c("❌ Kullanım: .time <ifade>", Colors.RED))
            return

        start = time.perf_counter()
        self._execute_source(code)
        elapsed = time.perf_counter() - start

        if elapsed < 0.001:
            time_str = f"{elapsed * 1_000_000:.1f} µs"
        elif elapsed < 1:
            time_str = f"{elapsed * 1_000:.2f} ms"
        else:
            time_str = f"{elapsed:.4f} s"

        print(self._c(f"⏱  Süre: {time_str}", Colors.YELLOW))

    def _cmd_ast(self, code: str) -> None:
        """Kodun AST yapısını göster."""
        if not code:
            print(self._c("❌ Kullanım: .ast <ifade>", Colors.RED))
            return

        try:
            lexer = Lexer(code, "<repl>")
            tokens = lexer.tokenize()
            parser = Parser(tokens)
            ast = parser.parse()
            self._print_ast(ast.body, indent=0)
        except Exception as e:
            print(self._c(f"❌ AST hatası: {e}", Colors.RED))

    def _print_ast(self, nodes, indent: int = 0) -> None:
        """AST düğümlerini ağaç yapısında yazdır."""
        prefix = "  " * indent
        for node in nodes:
            node_type = type(node).__name__
            info = ""
            if hasattr(node, 'name'):
                info = f" name={node.name!r}"
            elif hasattr(node, 'value') and not hasattr(node, 'body'):
                info = f" value={node.value!r}"
            elif hasattr(node, 'operator'):
                info = f" op={node.operator!r}"

            print(f"{prefix}{self._c('├─', Colors.GRAY)} {self._c(node_type, Colors.CYAN)}{self._c(info, Colors.YELLOW)}")

            # Alt düğümleri göster
            for attr in ['body', 'then_body', 'else_body', 'try_body', 'catch_body', 'finally_body']:
                child_body = getattr(node, attr, None)
                if child_body and isinstance(child_body, list):
                    print(f"{prefix}  {self._c(f'[{attr}]', Colors.GRAY)}")
                    self._print_ast(child_body, indent + 2)

            for attr in ['left', 'right', 'operand', 'condition', 'expression', 'value', 'callee']:
                child = getattr(node, attr, None)
                if child and hasattr(child, '__class__') and hasattr(child, 'location'):
                    self._print_ast([child], indent + 1)

    def _cmd_tokens(self, code: str) -> None:
        """Kodun token akışını göster."""
        if not code:
            print(self._c("❌ Kullanım: .tokens <ifade>", Colors.RED))
            return

        try:
            lexer = Lexer(code, "<repl>")
            tokens = lexer.tokenize()
            print(self._c("═══ Token Akışı ═══", Colors.CYAN))
            for tok in tokens:
                if tok.type.name == "EOF":
                    continue
                if tok.type.name in ("NEWLINE", "INDENT", "DEDENT"):
                    print(f"  {self._c(tok.type.name, Colors.GRAY)}")
                else:
                    val = f" = {tok.value!r}" if tok.value is not None else ""
                    print(f"  {self._c(tok.type.name, Colors.CYAN):30s} "
                          f"{self._c(tok.lexeme, Colors.WHITE)}{self._c(val, Colors.YELLOW)}")
        except Exception as e:
            print(self._c(f"❌ Token hatası: {e}", Colors.RED))

    def _cmd_reset(self) -> None:
        """Ortamı sıfırla."""
        self.evaluator = Evaluator()
        self.evaluator.ffi_bridge = self.ffi_bridge
        self.exec_count = 0
        print(self._c("🔄 Ortam sıfırlandı.", Colors.GREEN))

    # ─────────────────────────────────────────────────────
    # Kod Çalıştırma
    # ─────────────────────────────────────────────────────

    def _execute_source(self, source: str, filename: str = "<repl>") -> None:
        """Kaynak kodu lexer → parser → evaluator pipeline'ından geçir."""
        # 1. Lexical Analysis
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()

        if lexer.has_errors:
            for err in lexer.errors:
                print(self._c(f"  {translate('lexer_error')} {err}", Colors.RED))
            if ask_yes_no('auto_correct_prompt'):
                print(self._c(translate('auto_correcting'), Colors.YELLOW))
                source = autocorrect_source(source, lexer.errors)
                lexer = Lexer(source, filename)
                tokens = lexer.tokenize()
                if lexer.has_errors:
                    for err in lexer.errors:
                        print(self._c(f"  Lexer Hatası: {err}", Colors.RED))
                    print(self._c(translate('auto_correct_failed'), Colors.RED))
                    return
                print(self._c(translate('auto_corrected'), Colors.GREEN))
            else:
                return

        # 2. Parsing
        parser = Parser(tokens)
        ast = parser.parse()

        if parser.has_errors:
            for err in parser.errors:
                print(self._c(f"  Parser Hatası: {err}", Colors.RED))
            return

        # 3. Evaluation
        try:
            result = self.evaluator.execute(ast)

            # Sonucu göster (None değilse ve print/println değilse)
            if result is not None:
                formatted = self.evaluator._format_value(result)
                print(self._c(f"=> {formatted}", Colors.GREEN))

        except MRRRuntimeError as e:
            print(self._c(f"  Çalışma Hatası: {e}", Colors.RED))
        except KeyboardInterrupt:
            print(self._c("\n  ⚡ Kod iptal edildi.", Colors.YELLOW))
        except Exception as e:
            print(self._c(f"  Hata: {e}", Colors.RED))

    def _needs_continuation(self, source: str) -> bool:
        """Kod bloğu devam mı ediyor (çok satırlı giriş)?"""
        stripped = source.rstrip()
        if not stripped:
            return False
        # ':' ile biten satırlar blok başlatır
        if stripped.endswith(":"):
            return True
        # Açık parantezler
        open_count = source.count("(") - source.count(")")
        open_count += source.count("[") - source.count("]")
        open_count += source.count("{") - source.count("}")
        if open_count > 0:
            return True
        return False

    # ─────────────────────────────────────────────────────
    # Ana Döngü
    # ─────────────────────────────────────────────────────

    def run(self) -> None:
        """REPL ana döngüsünü başlat."""
        self._print_banner()

        while self.running:
            try:
                # Girdi oku
                try:
                    line = input(self._prompt())
                except EOFError:
                    # Ctrl+D
                    self.running = False
                    print(self._c("\n👋 MRR Terminali kapatılıyor...", Colors.YELLOW))
                    break

                # Boş satır atla
                if not line.strip():
                    continue

                # Geçmişe ekle
                self.history.append(line)

                # Dot komutu mu?
                if line.strip().startswith("."):
                    self._handle_dot_command(line.strip())
                    continue

                # Çok satırlı giriş kontrolü
                source = line
                if self._needs_continuation(source):
                    while True:
                        try:
                            cont = input(self._cont_prompt())
                        except EOFError:
                            break
                        if not cont.strip():
                            # Boş satır = blok sonu
                            break
                        source += "\n" + cont
                        if not self._needs_continuation(source):
                            # Parantezler kapandıysa ve ':' ile bitmiyorsa dur
                            if not cont.rstrip().endswith(":"):
                                break

                self.exec_count += 1
                self._execute_source(source)

            except KeyboardInterrupt:
                print(self._c("\n  ⚡ İptal (Ctrl+C). Çıkmak için .exit yazın.", Colors.YELLOW))
            except Exception as e:
                print(self._c(f"\n  Beklenmeyen Hata: {e}", Colors.RED))


# ═══════════════════════════════════════════════════════════
# ─── DOĞRUDAN ÇALIŞTIRMA ──────────────────────────────────
# ═══════════════════════════════════════════════════════════

def start_repl() -> None:
    """MRR REPL'i başlat."""
    repl = MRRREPL()
    repl.run()


if __name__ == "__main__":
    start_repl()
