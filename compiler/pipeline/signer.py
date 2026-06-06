"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Signer — Otomatik Dijital İmzalama Modülü                   ║
║                                                                  ║
║  LLVM ve Linker aşamasından sonra üretilen makine koduna (exe,   ║
║  sys, elf) otomatik dijital imza basar. Siber güvenlik ürünleri  ║
║  veya Kernel Driver (Ring-0) modüllerinin çalışabilmesi için     ║
║  dijital imza şarttır.                                           ║
║                                                                  ║
║  Özellikler:                                                    ║
║    - Windows: signtool.exe veya SignTool API kullanımı.          ║
║    - macOS: codesign CLI aracı.                                  ║
║    - Geliştirme (Dev) ortamları için otomatik Self-Signed        ║
║      sertifika oluşturma ve yükleme (PoC).                       ║
╚══════════════════════════════════════════════════════════════════╝
"""

import sys
import subprocess
import os

class MRRSigner:
    def __init__(self, cert_path: str = None, password: str = None):
        self.cert_path = cert_path
        self.password = password

    def _generate_test_cert_windows(self) -> str:
        """
        Windows için PowerShell üzerinden geçici (Self-Signed) bir
        Code Signing sertifikası oluşturur. (Sadece Test/Dev amaçlıdır)
        """
        print("[Signer] Test sertifikası üretiliyor (Windows)...")
        ps_cmd = (
            "$cert = New-SelfSignedCertificate -Type Custom -Subject 'CN=MRR Dev Root' "
            "-KeyUsage DigitalSignature -CertStoreLocation 'Cert:\\CurrentUser\\My' "
            "-TextExtension @('2.5.29.37={text}1.3.6.1.5.5.7.3.3'); "
            "Export-PfxCertificate -Cert $cert -FilePath 'mrr_dev.pfx' -Password (ConvertTo-SecureString -String 'mrr123' -Force -AsPlainText);"
        )
        try:
            subprocess.run(["powershell", "-Command", ps_cmd], check=True, capture_output=True)
            self.cert_path = "mrr_dev.pfx"
            self.password = "mrr123"
            print(f"[Signer] 'mrr_dev.pfx' başarıyla oluşturuldu.")
            return self.cert_path
        except subprocess.CalledProcessError as e:
            print(f"[Signer] Sertifika üretilemedi: {e.stderr}")
            return None

    def sign_executable(self, file_path: str) -> bool:
        """Belirtilen çalıştırılabilir dosyayı veya sürücüyü imzalar."""
        if not os.path.exists(file_path):
            print(f"[HATA] İmzalanacak dosya bulunamadı: {file_path}")
            return False

        print(f"[Signer] İmzalanıyor: {file_path}")

        if sys.platform == "win32":
            return self._sign_windows(file_path)
        elif sys.platform == "darwin":
            return self._sign_macos(file_path)
        else:
            print("[Signer] Linux üzerinde ELF dosyaları için imzalama şu an desteklenmiyor (Secure Boot/dm-verity harici).")
            return True

    def _sign_windows(self, file_path: str) -> bool:
        if not self.cert_path:
            # Geliştirici sertifikası yoksa test sertifikası üret
            self._generate_test_cert_windows()

        if not self.cert_path or not os.path.exists(self.cert_path):
            print("[Signer] ⚠ Sertifika bulunamadığı için imzalama atlanıyor.")
            return False

        # Not: Gerçek senaryoda signtool.exe'nin (Windows SDK) PATH'te olduğu varsayılır.
        # Burada PoC (Proof of Concept) olarak PowerShell komut setiyle SignTool simüle ediliyor.
        # PowerShell 'Set-AuthenticodeSignature' kullanılabilir.
        ps_cmd = (
            f"$cert = Get-PfxCertificate -FilePath '{self.cert_path}';"
            f"Set-AuthenticodeSignature -FilePath '{file_path}' -Certificate $cert"
        )
        
        try:
            res = subprocess.run(["powershell", "-Command", ps_cmd], capture_output=True, text=True)
            if "Valid" in res.stdout or res.returncode == 0:
                print("[Signer] ✓ Windows Authenticode İmzalama Başarılı.")
                return True
            else:
                print(f"[Signer] İmzalama başarısız: {res.stdout}")
                return False
        except Exception as e:
            print(f"[Signer] Hata: {e}")
            return False

    def _sign_macos(self, file_path: str) -> bool:
        # macOS codesign aracı
        identity = "Mac Developer" if not self.cert_path else self.cert_path
        try:
            subprocess.run(["codesign", "-s", identity, "-f", file_path], check=True)
            print("[Signer] ✓ macOS Codesign Başarılı.")
            return True
        except subprocess.CalledProcessError:
            print("[Signer] ⚠ codesign başarısız oldu. Geliştirici kimliği bulunamayabilir.")
            return False

def run_signer(executable_path: str, cert_path: str = None, password: str = None):
    signer = MRRSigner(cert_path, password)
    return signer.sign_executable(executable_path)
