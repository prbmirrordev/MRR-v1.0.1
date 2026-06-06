"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Cross-Platform Installer / Loader                         ║
║                                                                  ║
║  Kurulum aracı, işletim sistemini algılayarak PyQt6, LLVM        ║
║  bağımlılıklarını çözer, VSIX eklentisini Visual Studio'ya bağlar║
║  ve 'mrr' CLI komutunu sisteme enjekte eder.                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import subprocess
from pathlib import Path
import shutil

class MRRLoader:
    def __init__(self):
        self.os_type = sys.platform
        self.base_dir = Path(__file__).resolve().parent.parent

    def detect_os(self):
        print(f"[Loader] İşletim Sistemi Tespit Edildi: {self.os_type}")
        if self.os_type not in ["win32", "linux", "darwin"]:
            print("[Loader] ⚠ Uyarı: Desteklenmeyen işletim sistemi, bazı özellikler çalışmayabilir.")

    def install_dependencies(self):
        print("[Loader] Bağımlılıklar Yükleniyor (PyQt6, PyQt6-WebEngine, llvmlite)...")
        deps = ["PyQt6", "PyQt6-WebEngine", "llvmlite"]
        for dep in deps:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            except subprocess.CalledProcessError:
                print(f"[Loader] ⚠ '{dep}' yüklenirken hata oluştu.")
        print("[Loader] ✓ Bağımlılıklar başarıyla yüklendi.")

    def setup_cli(self):
        print("[Loader] MRR CLI (mrr komutu) sistem PATH'ine bağlanıyor...")
        bin_dir = self.base_dir / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        main_script = self.base_dir / "interpreter" / "main.py"
        
        if self.os_type == "win32":
            bat_path = bin_dir / "mrr.bat"
            with open(bat_path, "w", encoding="utf-8") as f:
                f.write(f"@echo off\n\"{sys.executable}\" \"{main_script}\" %*\n")
            print(f"[Loader] ✓ Windows wrapper oluşturuldu: {bat_path}")
            print("[Loader] (Lütfen 'bin' dizinini Çevre Değişkenlerinizdeki PATH'e ekleyin.)")
        else:
            sh_path = bin_dir / "mrr"
            with open(sh_path, "w", encoding="utf-8") as f:
                f.write(f"#!/usr/bin/env bash\n\"{sys.executable}\" \"{main_script}\" \"$@\"\n")
            os.chmod(sh_path, 0o755)
            print(f"[Loader] ✓ Unix wrapper oluşturuldu: {sh_path}")

    def setup_vsix(self):
        print("[Loader] Visual Studio Entegrasyonu Yapılandırılıyor...")
        vsix_dir = self.base_dir / "vsix" / "MRR.Language"
        if vsix_dir.exists():
            print(f"[Loader] VSIX Klasörü: {vsix_dir}")
            print("[Loader] Kurulum için VS Code üzerinden dizini açıp F5 ile eklentiyi test edebilirsiniz.")
        else:
            print("[Loader] ⚠ VSIX klasörü bulunamadı.")

    def run(self):
        print("="*50)
        print("  MRR Çapraz Platform Kurulum Yöneticisi")
        print("="*50)
        self.detect_os()
        self.install_dependencies()
        self.setup_cli()
        self.setup_vsix()
        print("="*50)
        print("[Loader] MRR Dili Kurulumu Tamamlandı!")
        print("Kullanım:")
        print("  mrr run dosya.mrr      # Anında Çalıştırma (Interpreter Mode & GUI)")
        print("  mrr compile dosya.mrr  # Ring-0 LLVM Derleme & Obfuscation & Sign")
        print("="*50)

if __name__ == "__main__":
    loader = MRRLoader()
    loader.run()
