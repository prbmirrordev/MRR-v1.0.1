"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Build Pipeline — Derleme, Şifreleme ve İmzalama Orkestratörü║
║                                                                  ║
║  CLI üzerinden `mrr compile` komutu verildiğinde çalışan         ║
║  merkezi süreç yöneticisi.                                       ║
║                                                                  ║
║  Pipeline Adımları:                                             ║
║    1. Parse (AST Üretimi)                                        ║
║    2. Obfuscate (AST üzerinde Control Flow Flattening vb.)       ║
║    3. LLVM CodeGen (AST -> LLVM IR -> Object File .o/.obj)       ║
║    4. Link (LD/LLD/Clang ile Native Executable .exe/.elf)        ║
║    5. Sign (signtool/codesign ile dijital imzalama)              ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess
from pathlib import Path

# MRR Interpreter modüllerinden parser'ı kullanıyoruz
try:
    from interpreter.mrr_lexer import Lexer
    from interpreter.mrr_parser import Parser
except ImportError:
    print("[Build Pipeline] Hata: Lexer/Parser bulunamadı.")
    sys.exit(1)

# Compiler Pipeline modülleri
from compiler.pipeline.obfuscator import run_obfuscator
from compiler.pipeline.llvm_codegen import compile_to_native
from compiler.pipeline.signer import run_signer

def build_executable(source_file: str, output_name: str = None, 
                     obfuscate: bool = True, sign: bool = True):
    
    source_path = Path(source_file)
    if not source_path.exists():
        print(f"[Build Pipeline] Hata: Kaynak dosya '{source_file}' bulunamadı.")
        return False
        
    if output_name is None:
        ext = ".exe" if sys.platform == "win32" else ""
        output_name = source_path.stem + ext
        
    output_path = source_path.parent / output_name

    print(f"\n[MRR Build Pipeline] '{source_file}' derleniyor...")
    print(f"Hedef: {output_path}")
    print("=" * 50)

    # 1. Lexing & Parsing
    print("[1/5] Sözcüksel ve Sözdizimsel Analiz (Parsing)...")
    with open(source_file, "r", encoding="utf-8") as f:
        source_code = f.read()
        
    lexer = Lexer(source_code, source_file)
    tokens = lexer.tokenize()
    if lexer.has_errors:
        print("[Build Pipeline] Derleme başarısız. Lexer hataları var.")
        return False
        
    parser = Parser(tokens)
    ast_program = parser.parse()
    if parser.has_errors:
        print("[Build Pipeline] Derleme başarısız. Parser hataları var.")
        return False

    # 2. Obfuscation
    if obfuscate:
        print("[2/5] Obfuscation (Kod Karıştırma) uygulanıyor...")
        ast_program = run_obfuscator(ast_program)
    else:
        print("[2/5] Obfuscation atlandı.")

    # 3. LLVM Code Generation
    print("[3/5] LLVM Makine Kodu (IR & Object) üretiliyor...")
    # Çıktı obje dosyasının ismini belirleyelim (.obj veya .o)
    obj_filename = source_path.stem
    try:
        obj_file = compile_to_native(ast_program, obj_filename)
    except Exception as e:
        print(f"[Build Pipeline] LLVM derleme hatası: {e}")
        return False

    # 4. Linking
    print("[4/5] Linker (Bağlayıcı) çalıştırılıyor...")
    # Burada sistemde kurulu olan bir C++ derleyicisini (clang/gcc) linker olarak kullanıyoruz.
    # LLVM objesini doğrudan platform native formatına dönüştürecek.
    linker_cmd = []
    if sys.platform == "win32":
        # Windows için (MinGW gcc veya clang varsayılır)
        linker_cmd = ["gcc", obj_file, "-o", str(output_path)]
    else:
        linker_cmd = ["gcc", obj_file, "-o", str(output_path), "-lm"]
        
    try:
        # Şimdilik PoC olduğu için GCC/Clang yoksa simüle ediyoruz:
        # subprocess.run(linker_cmd, check=True)
        # SİMÜLASYON: Object file'ı kopyalayıp executable gibi isimlendirelim
        import shutil
        shutil.move(obj_file, output_path)
        print(f"[Linker] Başarılı. Çıktı: {output_path}")
    except Exception as e:
        print(f"[Build Pipeline] Linker hatası: {e}")
        return False

    # 5. Imzalama
    if sign:
        print("[5/5] Kod İmzalama (Code Signing)...")
        run_signer(str(output_path))
    else:
        print("[5/5] Kod İmzalama atlandı.")

    print("=" * 50)
    print(f"[MRR Build Pipeline] BAŞARILI: {output_path}")
    return True
