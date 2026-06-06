"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Builder v1.0.1 — Build & Package System                    ║
║                                                                  ║
║  MRR projelerini standalone çalıştırılabilir dosyalara          ║
║  dönüştürür.                                                     ║
║                                                                  ║
║  Formatlar:                                                      ║
║    .mbuild  — MRR self-contained paket (ZIP tabanlı)            ║
║    .exe     — Native Windows executable (PyInstaller)           ║
║                                                                  ║
║  Kullanım:                                                       ║
║    mrr build proje.mrr --format mb    → proje.mbuild            ║
║    mrr build proje.mrr --format exe   → proje.exe               ║
║                                                                  ║
║  NOT: Profesyonel build için Java (MrrBuilder.java) ve          ║
║       C# (MrrBuilder.cs) araçları /builder dizininde yer alır.  ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import shutil
import zipfile
import subprocess
from pathlib import Path
from datetime import datetime


class MRRBuilder:
    """
    MRR Build System — .mbuild ve .exe formatlarını üretir.
    
    .mbuild: ZIP tabanlı self-contained paket. İçerik:
      - manifest.json  (metadata)
      - source/         (MRR kaynak dosyaları)
      - runtime/        (MRR interpreter + bağımlılıklar)
      - entry.py        (başlatıcı script)
    
    .exe: PyInstaller ile native Windows executable.
    
    Profesyonel kullanım için Java ve C# builder araçları
    /builder dizininde bulunur.
    """

    def __init__(self):
        self._mrr_root = Path(__file__).parent.parent
        self._version = "1.0.1"

    def build(self, source_file: str, fmt: str = "mb", output: str = None):
        """Ana build fonksiyonu."""
        source_path = Path(source_file).resolve()
        
        if not source_path.exists():
            print(f"\033[31m[HATA] Dosya bulunamadı: {source_file}\033[0m")
            sys.exit(1)

        if not source_path.suffix == ".mrr":
            print(f"\033[31m[HATA] .mrr dosyası bekleniyor: {source_file}\033[0m")
            sys.exit(1)

        project_name = source_path.stem
        
        if fmt == "mb":
            out_file = output or f"{project_name}.mbuild"
            self._build_mbuild(source_path, out_file, project_name)
        elif fmt == "exe":
            out_file = output or f"{project_name}.exe"
            self._build_exe(source_path, out_file, project_name)
        else:
            print(f"\033[31m[HATA] Bilinmeyen format: {fmt}\033[0m")
            sys.exit(1)

    def _build_mbuild(self, source_path: Path, out_file: str, project_name: str):
        """
        .mbuild formatında paket oluştur.
        
        .mbuild bir ZIP arşividir ve şunları içerir:
          - manifest.json
          - source/<dosya>.mrr
          - runtime/ (interpreter dosyaları)
          - entry.py (başlatıcı)
        """
        print(f"\n\033[36m╔══════════════════════════════════════════╗\033[0m")
        print(f"\033[36m║  MRR Builder v{self._version} — .mbuild Mode   ║\033[0m")
        print(f"\033[36m╚══════════════════════════════════════════╝\033[0m")
        print(f"\n  Kaynak:  {source_path}")
        print(f"  Çıktı:   {out_file}")
        print(f"  Format:  .mbuild (self-contained)")
        print()

        # Geçici build dizini
        build_dir = source_path.parent / f".mrr_build_{project_name}"
        if build_dir.exists():
            shutil.rmtree(build_dir)
        build_dir.mkdir(parents=True)

        try:
            # 1. Manifest oluştur
            print("  [1/4] Manifest oluşturuluyor...")
            manifest = {
                "name": project_name,
                "version": self._version,
                "entry": f"source/{source_path.name}",
                "runtime": "mrr",
                "runtime_version": self._version,
                "build_date": datetime.now().isoformat(),
                "platform": sys.platform,
                "python_version": sys.version.split()[0],
                "format": "mbuild",
                "format_version": "1.0",
            }
            manifest_path = build_dir / "manifest.json"
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

            # 2. Kaynak dosyayı kopyala
            print("  [2/4] Kaynak dosyalar kopyalanıyor...")
            source_dir = build_dir / "source"
            source_dir.mkdir()
            shutil.copy2(source_path, source_dir / source_path.name)

            # Aynı dizindeki diğer .mrr dosyalarını da ekle
            for mrr_file in source_path.parent.glob("*.mrr"):
                if mrr_file != source_path:
                    shutil.copy2(mrr_file, source_dir / mrr_file.name)

            # 3. Runtime'ı kopyala
            print("  [3/4] MRR Runtime paketleniyor...")
            runtime_dir = build_dir / "runtime"
            runtime_dir.mkdir()
            
            # Interpreter dosyalarını kopyala
            interp_src = self._mrr_root / "interpreter"
            if interp_src.exists():
                interp_dst = runtime_dir / "interpreter"
                shutil.copytree(
                    interp_src, interp_dst,
                    ignore=shutil.ignore_patterns(
                        "__pycache__", "*.pyc", "*.pyo", ".git"
                    )
                )

            # stdlib kopyala
            stdlib_src = self._mrr_root / "stdlib"
            if stdlib_src.exists():
                shutil.copytree(
                    stdlib_src, runtime_dir / "stdlib",
                    ignore=shutil.ignore_patterns("__pycache__")
                )

            # Entry point oluştur
            entry_content = f'''#!/usr/bin/env python3
"""MRR .mbuild Entry Point — Auto-generated by MRR Builder v{self._version}"""
import sys
import os

# Runtime'ı PATH'e ekle
runtime_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runtime")
sys.path.insert(0, runtime_dir)

# Kaynak dosyayı çalıştır
source_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source", "{source_path.name}")

from interpreter.mrr_lexer import Lexer
from interpreter.mrr_parser import Parser
from interpreter.mrr_evaluator import Evaluator
from interpreter.mrr_ffi import FFIBridge, SandboxPolicy

with open(source_file, "r", encoding="utf-8") as f:
    code = f.read()

lexer = Lexer(code, source_file)
tokens = lexer.tokenize()
parser = Parser(tokens)
ast = parser.parse()

ffi = FFIBridge(policy=SandboxPolicy())
evaluator = Evaluator()
evaluator.ffi_bridge = ffi
evaluator.execute(ast)
'''
            entry_path = build_dir / "entry.py"
            with open(entry_path, "w", encoding="utf-8") as f:
                f.write(entry_content)

            # 4. ZIP olarak paketle
            print("  [4/4] .mbuild arşivi oluşturuluyor...")
            out_path = source_path.parent / out_file
            with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(build_dir):
                    for file in files:
                        file_path = Path(root) / file
                        arcname = file_path.relative_to(build_dir)
                        zf.write(file_path, arcname)

            # Build dizinini temizle
            shutil.rmtree(build_dir)

            size_kb = out_path.stat().st_size / 1024
            print(f"\n\033[32m  ✓ Build başarılı!\033[0m")
            print(f"    Dosya: {out_path}")
            print(f"    Boyut: {size_kb:.1f} KB")
            print(f"\n    Çalıştırmak için: python -c \"import zipfile,sys; zipfile.ZipFile('{out_file}').extractall('.tmp_mrr'); exec(open('.tmp_mrr/entry.py').read())\"")

        except Exception as e:
            if build_dir.exists():
                shutil.rmtree(build_dir)
            print(f"\033[31m[HATA] Build başarısız: {e}\033[0m")
            sys.exit(1)

    def _build_exe(self, source_path: Path, out_file: str, project_name: str):
        """
        .exe formatında native executable oluştur.
        PyInstaller kullanır.
        """
        print(f"\n\033[36m╔══════════════════════════════════════════╗\033[0m")
        print(f"\033[36m║  MRR Builder v{self._version} — EXE Mode       ║\033[0m")
        print(f"\033[36m╚══════════════════════════════════════════╝\033[0m")
        print(f"\n  Kaynak:  {source_path}")
        print(f"  Çıktı:   {out_file}")
        print(f"  Format:  .exe (native Windows)")
        print()

        # Önce .mbuild oluştur, sonra PyInstaller ile paketle
        print("  [1/3] MRR paketi hazırlanıyor...")
        
        # Geçici wrapper script oluştur
        wrapper_path = source_path.parent / f"_mrr_build_{project_name}.py"
        
        wrapper_content = f'''#!/usr/bin/env python3
"""MRR EXE Wrapper — Auto-generated by MRR Builder v{self._version}"""
import sys
import os

# Interpreter'ı import edebilmek için path ayarla
mrr_root = r"{self._mrr_root}"
sys.path.insert(0, mrr_root)

from interpreter.mrr_lexer import Lexer
from interpreter.mrr_parser import Parser
from interpreter.mrr_evaluator import Evaluator
from interpreter.mrr_ffi import FFIBridge, SandboxPolicy

# Gömülü kaynak kod
SOURCE_CODE = """{self._read_source(source_path)}"""

lexer = Lexer(SOURCE_CODE, "{source_path.name}")
tokens = lexer.tokenize()
if lexer.has_errors:
    for e in lexer.errors:
        print(f"Hata: {{e}}")
    sys.exit(1)

parser = Parser(tokens)
ast = parser.parse()
if parser.has_errors:
    for e in parser.errors:
        print(f"Hata: {{e}}")
    sys.exit(1)

ffi = FFIBridge(policy=SandboxPolicy())
evaluator = Evaluator()
evaluator.ffi_bridge = ffi
evaluator.execute(ast)
'''
        
        with open(wrapper_path, "w", encoding="utf-8") as f:
            f.write(wrapper_content)

        print("  [2/3] PyInstaller ile derleniyor...")
        
        icon_path = self._mrr_root / "assets" / "mrr.ico"
        icon_arg = f"--icon={icon_path}" if icon_path.exists() else ""
        
        try:
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--name", project_name,
                "--distpath", str(source_path.parent),
                "--specpath", str(source_path.parent),
                "--workpath", str(source_path.parent / "build"),
                "--clean",
            ]
            if icon_arg:
                cmd.append(icon_arg)
            cmd.append(str(wrapper_path))
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"\033[33m  ⚠ PyInstaller bulunamadı veya hata oluştu.\033[0m")
                print(f"  Yüklemek için: pip install pyinstaller")
                print(f"\n  Alternatif: mrr build {source_path.name} --format mb")
            else:
                print(f"\n\033[32m  ✓ EXE build başarılı!\033[0m")
                exe_path = source_path.parent / f"{project_name}.exe"
                if exe_path.exists():
                    size_mb = exe_path.stat().st_size / (1024 * 1024)
                    print(f"    Dosya: {exe_path}")
                    print(f"    Boyut: {size_mb:.1f} MB")
        except FileNotFoundError:
            print(f"\033[33m  ⚠ PyInstaller bulunamadı.\033[0m")
            print(f"  Yüklemek için: pip install pyinstaller")
        finally:
            # Geçici dosyaları temizle
            if wrapper_path.exists():
                wrapper_path.unlink()
            build_dir = source_path.parent / "build"
            if build_dir.exists():
                shutil.rmtree(build_dir, ignore_errors=True)
            spec_file = source_path.parent / f"{project_name}.spec"
            if spec_file.exists():
                spec_file.unlink()

    def _read_source(self, path: Path) -> str:
        """Kaynak dosyayı oku ve escape et."""
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        # Triple-quote içinde kullanılacağı için escape et
        content = content.replace("\\", "\\\\")
        content = content.replace('"""', '\\"\\"\\"')
        return content
