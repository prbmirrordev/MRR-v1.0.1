"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Paket Yöneticisi — Package Manager                         ║
║                                                                  ║
║  NPM/Pip benzeri paket yönetim sistemi.                         ║
║  GitHub releases tabanlı paket dağıtımı.                        ║
║                                                                  ║
║  Komutlar:                                                       ║
║    mrr pkg init      — mrr.toml oluştur                          ║
║    mrr pkg install   — Paket yükle                               ║
║    mrr pkg remove    — Paket kaldır                              ║
║    mrr pkg list      — Paketleri listele                         ║
║    mrr pkg update    — Paketleri güncelle                        ║
║    mrr pkg publish   — Paketi yayınla                            ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import os
import sys
import json
import shutil
import urllib.request
import urllib.error
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


# ═══════════════════════════════════════════════════════════
# ─── VERİ YAPILARI ────────────────────────────────────────
# ═══════════════════════════════════════════════════════════

@dataclass
class PackageInfo:
    """Paket bilgileri."""
    name: str
    version: str
    description: str = ""
    author: str = ""
    license: str = "MIT"
    repository: str = ""
    dependencies: Dict[str, str] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    entry: str = "main.mrr"


@dataclass 
class InstalledPackage:
    """Yüklü paket bilgisi."""
    name: str
    version: str
    source: str  # GitHub URL veya yerel yol
    install_path: str


# ═══════════════════════════════════════════════════════════
# ─── MANIFEST PARSER (mrr.toml basit okuyucu) ────────────
# ═══════════════════════════════════════════════════════════

class ManifestParser:
    """
    Basit TOML-benzeri manifest dosyası okuyucu/yazıcı.
    Tam TOML desteği yerine MRR'a özel basit format.
    """

    @staticmethod
    def parse(filepath: str) -> PackageInfo:
        """mrr.toml dosyasını oku ve PackageInfo döndür."""
        data = {}
        current_section = None
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                
                # Boş satır veya yorum
                if not line or line.startswith('#'):
                    continue
                
                # Section başlığı [section]
                if line.startswith('[') and line.endswith(']'):
                    current_section = line[1:-1].strip()
                    if current_section not in data:
                        data[current_section] = {}
                    continue
                
                # Key = value
                if '=' in line:
                    key, _, value = line.partition('=')
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    if current_section:
                        data[current_section][key] = value
                    else:
                        data[key] = value
        
        pkg = data.get('package', {})
        deps = data.get('dependencies', {})
        
        return PackageInfo(
            name=pkg.get('name', 'unnamed'),
            version=pkg.get('version', '0.1.0'),
            description=pkg.get('description', ''),
            author=pkg.get('author', ''),
            license=pkg.get('license', 'MIT'),
            repository=pkg.get('repository', ''),
            dependencies=deps,
            keywords=[k.strip() for k in pkg.get('keywords', '').split(',') if k.strip()],
            entry=pkg.get('entry', 'main.mrr'),
        )

    @staticmethod
    def write(filepath: str, info: PackageInfo) -> None:
        """PackageInfo'yu mrr.toml dosyasına yaz."""
        lines = [
            '# MRR Paket Manifest Dosyası',
            '# https://github.com/mrr-lang/mrr',
            '',
            '[package]',
            f'name = "{info.name}"',
            f'version = "{info.version}"',
            f'description = "{info.description}"',
            f'author = "{info.author}"',
            f'license = "{info.license}"',
            f'entry = "{info.entry}"',
        ]
        
        if info.repository:
            lines.append(f'repository = "{info.repository}"')
        if info.keywords:
            lines.append(f'keywords = "{", ".join(info.keywords)}"')
        
        lines.extend(['', '[dependencies]'])
        for dep_name, dep_version in info.dependencies.items():
            lines.append(f'{dep_name} = "{dep_version}"')
        
        lines.append('')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))


# ═══════════════════════════════════════════════════════════
# ─── PAKET YÖNETİCİSİ ────────────────────────────────────
# ═══════════════════════════════════════════════════════════

class PackageManager:
    """
    MRR Paket Yöneticisi.
    
    Paketleri GitHub releases'dan indirir.
    Yerel cache: ~/.mrr/packages/
    Proje bağımlılıkları: ./mrr_packages/
    """

    GLOBAL_CACHE_DIR = Path.home() / '.mrr' / 'packages'
    REGISTRY_URL = "https://raw.githubusercontent.com/mrr-lang/registry/main/packages.json"
    
    def __init__(self, project_dir: str = "."):
        self.project_dir = Path(project_dir).resolve()
        self.packages_dir = self.project_dir / 'mrr_packages'
        self.manifest_path = self.project_dir / 'mrr.toml'
        self.lock_path = self.project_dir / 'mrr.lock'
        
        # Global cache
        self.GLOBAL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

    # ─────────────────────────────────────────────────────
    # init — Yeni proje başlat
    # ─────────────────────────────────────────────────────

    def init(self, name: Optional[str] = None) -> None:
        """Yeni MRR projesi başlat — mrr.toml oluştur."""
        if self.manifest_path.exists():
            print(f"[MRR-PKG] ⚠ mrr.toml zaten mevcut: {self.manifest_path}")
            return
        
        project_name = name or self.project_dir.name
        
        info = PackageInfo(
            name=project_name,
            version="0.1.0",
            description=f"{project_name} — MRR projesi",
            author="",
            license="MIT",
            entry="main.mrr",
        )
        
        ManifestParser.write(str(self.manifest_path), info)
        print(f"[MRR-PKG] ✓ mrr.toml oluşturuldu: {self.manifest_path}")
        
        # Temel dosya yapısını oluştur
        main_file = self.project_dir / 'main.mrr'
        if not main_file.exists():
            main_file.write_text(
                '/// MRR Projesi — Ana Giriş Noktası\n'
                '/// Proje: ' + project_name + '\n'
                '\n'
                'println("Merhaba, MRR!")\n',
                encoding='utf-8'
            )
            print(f"[MRR-PKG] ✓ main.mrr oluşturuldu")
        
        # .gitignore
        gitignore = self.project_dir / '.gitignore'
        if not gitignore.exists():
            gitignore.write_text(
                '# MRR\n'
                'mrr_packages/\n'
                '*.pyc\n'
                '__pycache__/\n'
                '.mrr_cache/\n'
                '*.exe\n'
                '*.dll\n'
                '*.so\n',
                encoding='utf-8'
            )
            print(f"[MRR-PKG] ✓ .gitignore oluşturuldu")

    # ─────────────────────────────────────────────────────
    # install — Paket yükle
    # ─────────────────────────────────────────────────────

    def install(self, package_spec: str) -> bool:
        """
        Paket yükle.
        
        Format:
          mrr pkg install <name>               — Registry'den
          mrr pkg install <github_user/repo>   — GitHub'dan
          mrr pkg install <path>               — Yerel dizinden
        """
        print(f"[MRR-PKG] Yükleniyor: {package_spec}")
        
        # GitHub URL kontrolü
        if '/' in package_spec and not os.path.exists(package_spec):
            return self._install_from_github(package_spec)
        
        # Yerel dizin kontrolü
        if os.path.isdir(package_spec):
            return self._install_from_local(package_spec)
        
        # Registry'den yükleme
        return self._install_from_registry(package_spec)

    def _install_from_github(self, repo: str) -> bool:
        """GitHub repository'sinden paket yükle."""
        # repo format: user/repo veya user/repo@version
        version = "latest"
        if '@' in repo:
            repo, version = repo.rsplit('@', 1)
        
        if version == "latest":
            api_url = f"https://api.github.com/repos/{repo}/releases/latest"
        else:
            api_url = f"https://api.github.com/repos/{repo}/releases/tags/v{version}"
        
        try:
            req = urllib.request.Request(api_url, headers={
                'User-Agent': 'MRR-PackageManager/1.0',
                'Accept': 'application/vnd.github.v3+json'
            })
            with urllib.request.urlopen(req, timeout=30) as response:
                release_data = json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            print(f"[MRR-PKG] ✗ GitHub API hatası: {e.code}")
            return False
        except Exception as e:
            print(f"[MRR-PKG] ✗ Bağlantı hatası: {e}")
            return False
        
        # ZIP asset'ini bul
        zip_url = release_data.get('zipball_url')
        if not zip_url:
            print(f"[MRR-PKG] ✗ Release ZIP bulunamadı")
            return False
        
        # İndir ve çıkart
        pkg_name = repo.split('/')[-1]
        return self._download_and_extract(zip_url, pkg_name, release_data.get('tag_name', version))

    def _install_from_local(self, path: str) -> bool:
        """Yerel dizinden paket yükle."""
        src = Path(path).resolve()
        manifest = src / 'mrr.toml'
        
        if not manifest.exists():
            print(f"[MRR-PKG] ✗ mrr.toml bulunamadı: {manifest}")
            return False
        
        info = ManifestParser.parse(str(manifest))
        dest = self.packages_dir / info.name
        
        if dest.exists():
            shutil.rmtree(dest)
        
        shutil.copytree(src, dest, ignore=shutil.ignore_patterns(
            'mrr_packages', '__pycache__', '*.pyc', '.git'
        ))
        
        self._update_manifest_deps(info.name, info.version)
        self._update_lock(info.name, info.version, str(src))
        
        print(f"[MRR-PKG] ✓ {info.name}@{info.version} yüklendi (yerel)")
        return True

    def _install_from_registry(self, name: str) -> bool:
        """MRR registry'sinden paket yükle."""
        print(f"[MRR-PKG] Registry'de aranıyor: {name}")
        
        # Registry henüz yoksa, GitHub'da ara
        github_search = f"mrr-lang/{name}"
        return self._install_from_github(github_search)

    def _download_and_extract(self, url: str, name: str, version: str) -> bool:
        """URL'den ZIP indir ve çıkart."""
        self.packages_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'MRR-PackageManager/1.0'
            })
            
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp:
                with urllib.request.urlopen(req, timeout=60) as response:
                    shutil.copyfileobj(response, tmp)
                tmp_path = tmp.name
            
            # ZIP'i çıkart
            dest = self.packages_dir / name
            if dest.exists():
                shutil.rmtree(dest)
            
            with zipfile.ZipFile(tmp_path, 'r') as zf:
                # GitHub ZIP'leri genellikle bir üst dizin içerir
                members = zf.namelist()
                prefix = members[0].split('/')[0] if members else ''
                
                dest.mkdir(parents=True, exist_ok=True)
                for member in members:
                    if member.endswith('/'):
                        continue
                    # Üst dizini kaldır
                    relative = member[len(prefix):].lstrip('/')
                    if not relative:
                        continue
                    target = dest / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, 'wb') as dst:
                        shutil.copyfileobj(src, dst)
            
            os.unlink(tmp_path)
            
            self._update_manifest_deps(name, version)
            self._update_lock(name, version, url)
            
            print(f"[MRR-PKG] ✓ {name}@{version} yüklendi")
            return True
            
        except Exception as e:
            print(f"[MRR-PKG] ✗ İndirme hatası: {e}")
            return False

    # ─────────────────────────────────────────────────────
    # remove — Paket kaldır
    # ─────────────────────────────────────────────────────

    def remove(self, name: str) -> bool:
        """Paketi kaldır."""
        pkg_dir = self.packages_dir / name
        
        if not pkg_dir.exists():
            print(f"[MRR-PKG] ✗ Paket bulunamadı: {name}")
            return False
        
        shutil.rmtree(pkg_dir)
        self._remove_from_manifest(name)
        self._remove_from_lock(name)
        
        print(f"[MRR-PKG] ✓ {name} kaldırıldı")
        return True

    # ─────────────────────────────────────────────────────
    # list — Paketleri listele
    # ─────────────────────────────────────────────────────

    def list_packages(self) -> List[InstalledPackage]:
        """Yüklü paketleri listele."""
        packages = []
        
        if not self.packages_dir.exists():
            print("[MRR-PKG] Yüklü paket yok.")
            return packages
        
        for pkg_dir in self.packages_dir.iterdir():
            if not pkg_dir.is_dir():
                continue
            
            manifest = pkg_dir / 'mrr.toml'
            if manifest.exists():
                info = ManifestParser.parse(str(manifest))
                pkg = InstalledPackage(
                    name=info.name,
                    version=info.version,
                    source=info.repository or "local",
                    install_path=str(pkg_dir)
                )
            else:
                pkg = InstalledPackage(
                    name=pkg_dir.name,
                    version="unknown",
                    source="unknown",
                    install_path=str(pkg_dir)
                )
            
            packages.append(pkg)
            print(f"  📦 {pkg.name}@{pkg.version} ({pkg.source})")
        
        if not packages:
            print("[MRR-PKG] Yüklü paket yok.")
        else:
            print(f"\n[MRR-PKG] Toplam {len(packages)} paket yüklü.")
        
        return packages

    # ─────────────────────────────────────────────────────
    # Manifest ve Lock Yönetimi
    # ─────────────────────────────────────────────────────

    def _update_manifest_deps(self, name: str, version: str) -> None:
        """mrr.toml'daki bağımlılıkları güncelle."""
        if not self.manifest_path.exists():
            return
        
        info = ManifestParser.parse(str(self.manifest_path))
        info.dependencies[name] = version
        ManifestParser.write(str(self.manifest_path), info)

    def _remove_from_manifest(self, name: str) -> None:
        """mrr.toml'dan bağımlılığı kaldır."""
        if not self.manifest_path.exists():
            return
        
        info = ManifestParser.parse(str(self.manifest_path))
        info.dependencies.pop(name, None)
        ManifestParser.write(str(self.manifest_path), info)

    def _update_lock(self, name: str, version: str, source: str) -> None:
        """mrr.lock dosyasını güncelle."""
        lock_data = {}
        if self.lock_path.exists():
            try:
                lock_data = json.loads(self.lock_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                lock_data = {}
        
        if 'packages' not in lock_data:
            lock_data['packages'] = {}
        
        lock_data['packages'][name] = {
            'version': version,
            'source': source,
        }
        
        self.lock_path.write_text(
            json.dumps(lock_data, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def _remove_from_lock(self, name: str) -> None:
        """mrr.lock'dan paketi kaldır."""
        if not self.lock_path.exists():
            return
        
        try:
            lock_data = json.loads(self.lock_path.read_text(encoding='utf-8'))
            lock_data.get('packages', {}).pop(name, None)
            self.lock_path.write_text(
                json.dumps(lock_data, indent=2, ensure_ascii=False),
                encoding='utf-8'
            )
        except json.JSONDecodeError:
            pass


# ═══════════════════════════════════════════════════════════
# ─── CLI GİRİŞ NOKTASI ───────────────────────────────────
# ═══════════════════════════════════════════════════════════

def pkg_cli(args: list) -> int:
    """Paket yöneticisi CLI."""
    if not args:
        print("MRR Paket Yöneticisi")
        print("Kullanım:")
        print("  mrr pkg init [name]       — Yeni proje oluştur")
        print("  mrr pkg install <paket>   — Paket yükle")
        print("  mrr pkg remove <paket>    — Paket kaldır")
        print("  mrr pkg list              — Paketleri listele")
        print("  mrr pkg update            — Paketleri güncelle")
        return 0
    
    pm = PackageManager()
    command = args[0]
    
    if command == 'init':
        name = args[1] if len(args) > 1 else None
        pm.init(name)
        return 0
    
    elif command == 'install':
        if len(args) < 2:
            print("[MRR-PKG] ✗ Paket adı gerekli: mrr pkg install <paket>")
            return 1
        success = pm.install(args[1])
        return 0 if success else 1
    
    elif command == 'remove':
        if len(args) < 2:
            print("[MRR-PKG] ✗ Paket adı gerekli: mrr pkg remove <paket>")
            return 1
        success = pm.remove(args[1])
        return 0 if success else 1
    
    elif command == 'list':
        pm.list_packages()
        return 0
    
    elif command == 'update':
        print("[MRR-PKG] Güncelleme kontrol ediliyor...")
        # Tüm paketleri yeniden yükle
        if pm.manifest_path.exists():
            info = ManifestParser.parse(str(pm.manifest_path))
            for dep_name in info.dependencies:
                pm.install(dep_name)
        return 0
    
    else:
        print(f"[MRR-PKG] ✗ Bilinmeyen komut: {command}")
        return 1
