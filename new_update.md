# MRR v1.0.1 — "Resilient" Güncelleme Notları
# MRR v1.0.1 — "Resilient" Release Notes

---

## 🇹🇷 Türkçe

### 🎯 Bu güncellemenin amacı

MRR 1.0.1 "Resilient", dilin kırılganlığını ortadan kaldırmak ve daha sağlam, daha profesyonel bir geliştirme deneyimi sunmak amacıyla çıkarıldı.

### ✅ Değişiklikler

#### 🛡️ Token Hatası Düzeltmeleri (Kritik)
- **Case-insensitive komut tanıma:** `Fonction.create`, `fonction.create`, `FONCTION.CREATE` artık hepsi aynı şekilde tanınır
- **Case-insensitive anahtar kelimeler:** `If`, `IF`, `if` hepsi çalışır — uyarı verilir ama çökmez
- **BOM desteği:** UTF-8 BOM karakteri olan dosyalar artık sorunsuz açılır
- **Hata kurtarma:** Lexer beklenmeyen karakter gördüğünde çökmek yerine ERROR token üretir ve devam eder
- **Kırmızı kutu hata gösterimi:** Hatalar artık terminal ve editörde kırmızı kutu içinde gösterilir

#### 🔧 Parser Geliştirmeleri
- **Gelişmiş senkronizasyon:** 20+ farklı token tipinde senkronize olabilir
- **Toleranslı token tüketimi:** Eksik `:` gibi durumlarda uyarı verir ama çökmez
- **Parser uyarı sistemi:** Toleranslı ayrıştırma sonucu oluşan uyarılar raporlanır

#### ⚡ ring-1 Kütüphanesi (YENİ)
- Pre-boot execution layer — BIOS/UEFI öncesi çalışma konsepti
- **armrrOS:** İçerisinde bulunan mikro işletim sistemi (kavramsal)
- Fonksiyonlar: `boot()`, `init()`, `shutdown()`, `status()`, `memory_map()`, `cpu_info()`
- `add.code "ring1"` ile kullanılabilir

#### 📦 .mbuild Build Sistemi (YENİ)
- **Java MrrBuilder:** Profesyonel .mbuild paket oluşturma (`builder/MrrBuilder.java`)
- **C# MrrBuilder:** Native .exe oluşturma (`builder/MrrBuilder.cs`)
- **Python Builder:** `mrr build dosya.mrr --format mb|exe` komutu
- .mbuild formatı: ZIP tabanlı self-contained paket — MRR kurulu olmadan çalışır

#### ⚙️ Java Optimizer (YENİ)
- MRR kodunu optimize eden Java aracı (`optimizer/MrrOptimizer.java`)
- Sabit katlama (Constant Folding)
- Ölü kod eleme (Dead Code Elimination)
- Güç azaltma (Strength Reduction)
- Sabit yayılımı (Constant Propagation)
- Boşluk temizleme

#### 🐧 Linux Installer (YENİ)
- `kalinstall.sh` — Kali Linux, Ubuntu, Debian desteği
- Otomatik Python bağımlılık kontrolü
- PATH entegrasyonu (.bashrc, .zshrc, fish)
- Otomatik editör tespiti ve eklenti kurulumu:
  - VS Code, VS Code Insiders, VSCodium, Cursor
  - Vim, Neovim (syntax highlighting)
  - Sublime Text

#### 🖥️ VS Code Extension Geliştirmeleri
- **Live Diagnostics:** Kod yazarken anlık hata tespiti
- Büyük/küçük harf hataları kırmızı altı çizgi ile gösterilir
- MRR lexer ve parser entegrasyonu ile gerçek zamanlı hata raporlama
- Sürüm: 0.2.0

#### 📋 Diğer
- Versiyon: 1.0.0 → 1.0.1
- Codename: Shadow → Resilient
- install.ps1 güncellemesi (editör tespiti eklendi)
- mrr.bat güncellemesi (build komutu eklendi)

### 📁 Yeni Dosyalar
```
stdlib/ring1/ring1.mrr       — ring-1 kütüphanesi (armrrOS)
builder/MrrBuilder.java      — Java build aracı
builder/MrrBuilder.cs        — C# build aracı
optimizer/MrrOptimizer.java  — Java optimizer
interpreter/mrr_builder.py   — Python build modülü
kalinstall.sh                — Linux installer
new_update.md                — Bu dosya
```

---

## 🇬🇧 English

### 🎯 Purpose of this update

MRR 1.0.1 "Resilient" was released to eliminate the fragility of the language and deliver a more robust, more professional development experience.

### ✅ Changes

#### 🛡️ Token Error Fixes (Critical)
- **Case-insensitive command recognition:** `Fonction.create`, `fonction.create`, `FONCTION.CREATE` all work
- **Case-insensitive keywords:** `If`, `IF`, `if` all work — warning is shown but no crash
- **BOM support:** Files with UTF-8 BOM are now handled seamlessly
- **Error recovery:** Lexer produces ERROR tokens instead of crashing on unexpected characters
- **Red box error display:** Errors are now shown in red boxes in terminal and editor

#### 🔧 Parser Improvements
- **Enhanced synchronization:** Can synchronize on 20+ different token types
- **Tolerant token consumption:** Missing `:` produces a warning but doesn't crash
- **Parser warning system:** Warnings from tolerant parsing are reported

#### ⚡ ring-1 Library (NEW)
- Pre-boot execution layer — runs before BIOS/OS
- **armrrOS:** Embedded micro operating system concept
- Functions: `boot()`, `init()`, `shutdown()`, `status()`, `memory_map()`, `cpu_info()`
- Use with `add.code "ring1"`

#### 📦 .mbuild Build System (NEW)
- **Java MrrBuilder:** Professional .mbuild package builder (`builder/MrrBuilder.java`)
- **C# MrrBuilder:** Native .exe builder (`builder/MrrBuilder.cs`)
- **Python Builder:** `mrr build file.mrr --format mb|exe` command
- .mbuild format: ZIP-based self-contained package — runs without MRR installed

#### ⚙️ Java Optimizer (NEW)
- Java-based MRR code optimizer (`optimizer/MrrOptimizer.java`)
- Constant Folding, Dead Code Elimination, Strength Reduction
- Constant Propagation, Whitespace Cleanup

#### 🐧 Linux Installer (NEW)
- `kalinstall.sh` — Kali Linux, Ubuntu, Debian support
- Auto Python dependency check, PATH integration
- Auto editor detection & extension install (VS Code, Vim, Neovim, Sublime)

#### 🖥️ VS Code Extension Improvements
- **Live Diagnostics:** Real-time error detection while typing
- Case errors shown with red underline
- Version: 0.2.0

---

## ⬆️ Güncelleme / Upgrade

### Windows
```powershell
# Mevcut dizinde güncelle
.\install.ps1
```

### Linux (Kali/Ubuntu/Debian)
```bash
chmod +x kalinstall.sh
sudo ./kalinstall.sh
```

---

**MRR v1.0.1 "Resilient" — Daha sağlam, daha güçlü, daha profesyonel.**
