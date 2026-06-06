#!/bin/bash
# ╔══════════════════════════════════════════════════════════════════╗
# ║  MRR Installer — Kali Linux / Ubuntu / Debian                   ║
# ║  Version: 1.0.1 Resilient                                       ║
# ║                                                                  ║
# ║  Bu script MRR dilini Linux sistemine kurar:                     ║
# ║    1. Python bağımlılıklarını kontrol eder                       ║
# ║    2. MRR'yi /usr/local/lib/mrr'ye kopyalar                     ║
# ║    3. mrr komutunu PATH'e ekler                                  ║
# ║    4. Editör eklentilerini otomatik kurar                        ║
# ║    5. .mrr dosya ilişkilendirmesi yapar                          ║
# ║                                                                  ║
# ║  Kullanım:                                                      ║
# ║    chmod +x kalinstall.sh                                        ║
# ║    sudo ./kalinstall.sh                                          ║
# ╚══════════════════════════════════════════════════════════════════╝

set -e

# ─── Renk Tanımları ───
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ─── Sabitler ───
MRR_VERSION="1.0.1"
MRR_INSTALL_DIR="/usr/local/lib/mrr"
MRR_BIN="/usr/local/bin/mrr"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# ─────────────────────────────────────────────────────
# Banner
# ─────────────────────────────────────────────────────

print_banner() {
    echo -e "${CYAN}"
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  MRR — Memory, Registers, Rings                     ║"
    echo "║  Offensive Security Programming Language             ║"
    echo "║  Version: ${MRR_VERSION} (Resilient)                        ║"
    echo "║  Linux Installer                                     ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# ─────────────────────────────────────────────────────
# Root Kontrolü
# ─────────────────────────────────────────────────────

check_root() {
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}[HATA] Bu script root yetkisi gerektirir.${NC}"
        echo "  sudo ./kalinstall.sh"
        exit 1
    fi
}

# ─────────────────────────────────────────────────────
# Python Kontrolü
# ─────────────────────────────────────────────────────

check_python() {
    echo -e "${BOLD}[1/6] Python kontrolü...${NC}"
    
    if command -v python3 &>/dev/null; then
        PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
        echo -e "  ${GREEN}✓ Python ${PY_VERSION} bulundu${NC}"
    else
        echo -e "  ${YELLOW}⚠ Python3 bulunamadı. Kuruluyor...${NC}"
        
        if command -v apt-get &>/dev/null; then
            apt-get update -qq
            apt-get install -y python3 python3-pip
        elif command -v pacman &>/dev/null; then
            pacman -Sy --noconfirm python python-pip
        elif command -v dnf &>/dev/null; then
            dnf install -y python3 python3-pip
        else
            echo -e "${RED}[HATA] Paket yöneticisi bulunamadı. Python3'ü elle kurun.${NC}"
            exit 1
        fi
        
        echo -e "  ${GREEN}✓ Python kuruldu${NC}"
    fi
}

# ─────────────────────────────────────────────────────
# MRR Dosyalarını Kopyala
# ─────────────────────────────────────────────────────

install_mrr() {
    echo -e "${BOLD}[2/6] MRR dosyaları kuruluyor...${NC}"
    
    # Eski kurulumu temizle
    if [ -d "$MRR_INSTALL_DIR" ]; then
        echo "  Eski kurulum temizleniyor..."
        rm -rf "$MRR_INSTALL_DIR"
    fi
    
    # Dosyaları kopyala
    mkdir -p "$MRR_INSTALL_DIR"
    cp -r "$SCRIPT_DIR/interpreter" "$MRR_INSTALL_DIR/"
    cp -r "$SCRIPT_DIR/stdlib" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/compiler" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/runtime" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/optimizer" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/builder" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/assets" "$MRR_INSTALL_DIR/" 2>/dev/null || true
    
    echo -e "  ${GREEN}✓ MRR dosyaları kopyalandı: ${MRR_INSTALL_DIR}${NC}"
}

# ─────────────────────────────────────────────────────
# mrr Komutunu Oluştur
# ─────────────────────────────────────────────────────

create_launcher() {
    echo -e "${BOLD}[3/6] mrr komutu oluşturuluyor...${NC}"
    
    cat > "$MRR_BIN" << 'LAUNCHER'
#!/bin/bash
# MRR Language Launcher v1.0.1
MRR_ROOT="/usr/local/lib/mrr"
export PYTHONPATH="$MRR_ROOT:$PYTHONPATH"

if [ $# -eq 0 ]; then
    echo "╔══════════════════════════════════════════════════════╗"
    echo "║  MRR — Memory, Registers, Rings v1.0.1 Resilient   ║"
    echo "║  Offensive Security Programming Language             ║"
    echo "╚══════════════════════════════════════════════════════╝"
    echo ""
    echo "  Kullanım: mrr <komut> [seçenekler] [argümanlar]"
    echo ""
    echo "  Komutlar:"
    echo "    run <dosya.mrr>        Dosyayı çalıştır"
    echo "    build <dosya.mrr>      .mbuild veya .exe oluştur"
    echo "    compile <dosya.mrr>    Makine koduna derle"
    echo "    check <dosya.mrr>      Syntax kontrolü"
    echo "    format <dosya.mrr>     Kodu formatla"
    echo "    init [ad]              Yeni proje oluştur"
    echo "    pkg <alt_komut>        Paket yöneticisi"
    echo "    repl                   İnteraktif terminal"
    echo "    version                Sürüm bilgisi"
    echo ""
    exit 0
fi

# İlk argüman bir dosya ise doğrudan çalıştır
if [ -f "$1" ] && [[ "$1" == *.mrr ]]; then
    python3 -m interpreter.main run "$@"
    exit $?
fi

python3 -m interpreter.main "$@"
LAUNCHER

    chmod +x "$MRR_BIN"
    echo -e "  ${GREEN}✓ mrr komutu oluşturuldu: ${MRR_BIN}${NC}"
}

# ─────────────────────────────────────────────────────
# PATH Entegrasyonu
# ─────────────────────────────────────────────────────

setup_path() {
    echo -e "${BOLD}[4/6] PATH entegrasyonu...${NC}"
    
    # /usr/local/bin zaten PATH'te olmalı ama kontrol et
    REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
    REAL_HOME=$(eval echo "~$REAL_USER")
    
    # .bashrc
    if [ -f "$REAL_HOME/.bashrc" ]; then
        if ! grep -q "MRR_ROOT" "$REAL_HOME/.bashrc" 2>/dev/null; then
            echo "" >> "$REAL_HOME/.bashrc"
            echo "# MRR Programming Language" >> "$REAL_HOME/.bashrc"
            echo "export MRR_ROOT=\"$MRR_INSTALL_DIR\"" >> "$REAL_HOME/.bashrc"
            echo "export PATH=\"\$PATH:/usr/local/bin\"" >> "$REAL_HOME/.bashrc"
            echo -e "  ${GREEN}✓ .bashrc güncellendi${NC}"
        else
            echo -e "  ${YELLOW}○ .bashrc zaten güncel${NC}"
        fi
    fi
    
    # .zshrc
    if [ -f "$REAL_HOME/.zshrc" ]; then
        if ! grep -q "MRR_ROOT" "$REAL_HOME/.zshrc" 2>/dev/null; then
            echo "" >> "$REAL_HOME/.zshrc"
            echo "# MRR Programming Language" >> "$REAL_HOME/.zshrc"
            echo "export MRR_ROOT=\"$MRR_INSTALL_DIR\"" >> "$REAL_HOME/.zshrc"
            echo "export PATH=\"\$PATH:/usr/local/bin\"" >> "$REAL_HOME/.zshrc"
            echo -e "  ${GREEN}✓ .zshrc güncellendi${NC}"
        else
            echo -e "  ${YELLOW}○ .zshrc zaten güncel${NC}"
        fi
    fi
    
    # Fish shell
    FISH_CONFIG="$REAL_HOME/.config/fish/config.fish"
    if [ -f "$FISH_CONFIG" ]; then
        if ! grep -q "MRR_ROOT" "$FISH_CONFIG" 2>/dev/null; then
            echo "" >> "$FISH_CONFIG"
            echo "# MRR Programming Language" >> "$FISH_CONFIG"
            echo "set -x MRR_ROOT $MRR_INSTALL_DIR" >> "$FISH_CONFIG"
            echo -e "  ${GREEN}✓ fish config güncellendi${NC}"
        fi
    fi
}

# ─────────────────────────────────────────────────────
# Editör Eklentisi Kurulumu
# ─────────────────────────────────────────────────────

install_editor_extensions() {
    echo -e "${BOLD}[5/6] Editör eklentileri kontrol ediliyor...${NC}"
    
    VSIX_PATH="$SCRIPT_DIR/vsix/MRR.Language/mrr-language-support-0.1.0.vsix"
    REAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo root)}"
    
    # VS Code
    if command -v code &>/dev/null; then
        echo -e "  ${CYAN}→ VS Code tespit edildi${NC}"
        if [ -f "$VSIX_PATH" ]; then
            sudo -u "$REAL_USER" code --install-extension "$VSIX_PATH" --force 2>/dev/null || true
            echo -e "  ${GREEN}✓ VS Code eklentisi kuruldu${NC}"
        fi
    fi
    
    # VS Code Insiders
    if command -v code-insiders &>/dev/null; then
        echo -e "  ${CYAN}→ VS Code Insiders tespit edildi${NC}"
        if [ -f "$VSIX_PATH" ]; then
            sudo -u "$REAL_USER" code-insiders --install-extension "$VSIX_PATH" --force 2>/dev/null || true
            echo -e "  ${GREEN}✓ VS Code Insiders eklentisi kuruldu${NC}"
        fi
    fi
    
    # VSCodium
    if command -v codium &>/dev/null; then
        echo -e "  ${CYAN}→ VSCodium tespit edildi${NC}"
        if [ -f "$VSIX_PATH" ]; then
            sudo -u "$REAL_USER" codium --install-extension "$VSIX_PATH" --force 2>/dev/null || true
            echo -e "  ${GREEN}✓ VSCodium eklentisi kuruldu${NC}"
        fi
    fi

    # Cursor
    if command -v cursor &>/dev/null; then
        echo -e "  ${CYAN}→ Cursor tespit edildi${NC}"
        if [ -f "$VSIX_PATH" ]; then
            sudo -u "$REAL_USER" cursor --install-extension "$VSIX_PATH" --force 2>/dev/null || true
            echo -e "  ${GREEN}✓ Cursor eklentisi kuruldu${NC}"
        fi
    fi
    
    # Vim/Neovim — syntax dosyası oluştur
    REAL_HOME=$(eval echo "~$REAL_USER")
    if command -v vim &>/dev/null || command -v nvim &>/dev/null; then
        echo -e "  ${CYAN}→ Vim/Neovim tespit edildi${NC}"
        
        VIM_SYNTAX_DIR="$REAL_HOME/.vim/syntax"
        VIM_FTDETECT_DIR="$REAL_HOME/.vim/ftdetect"
        mkdir -p "$VIM_SYNTAX_DIR" "$VIM_FTDETECT_DIR"
        
        # ftdetect
        cat > "$VIM_FTDETECT_DIR/mrr.vim" << 'VIM_FT'
au BufNewFile,BufRead *.mrr set filetype=mrr
VIM_FT
        
        # Basit syntax highlighting
        cat > "$VIM_SYNTAX_DIR/mrr.vim" << 'VIM_SYN'
" MRR Syntax File
if exists("b:current_syntax")
    finish
endif

syn keyword mrrKeyword Fonction Function fn let mut const if elif else for while loop match return break continue pass struct class trait impl pub unsafe kernel ring0 exploit hook driver enum try catch finally throw do defer delete use module as in is not and or true false null print println add
syn keyword mrrType i8 i16 i32 i64 u8 u16 u32 u64 f32 f64 str bool byte void
syn match mrrComment "//.*$"
syn match mrrComment "#.*$"
syn region mrrString start='"' end='"'
syn match mrrNumber "\<\d\+\>"
syn match mrrOperator "[+\-*/%=<>!&|^~]"
syn match mrrCommand "\<\(Fonction\|Function\|add\)\.\w\+"

hi def link mrrKeyword Statement
hi def link mrrType Type
hi def link mrrComment Comment
hi def link mrrString String
hi def link mrrNumber Number
hi def link mrrOperator Operator
hi def link mrrCommand Special

let b:current_syntax = "mrr"
VIM_SYN
        
        chown -R "$REAL_USER:$REAL_USER" "$REAL_HOME/.vim" 2>/dev/null || true
        echo -e "  ${GREEN}✓ Vim syntax dosyası kuruldu${NC}"
        
        # Neovim
        if command -v nvim &>/dev/null; then
            NVIM_DIR="$REAL_HOME/.config/nvim"
            mkdir -p "$NVIM_DIR/syntax" "$NVIM_DIR/ftdetect"
            cp "$VIM_FTDETECT_DIR/mrr.vim" "$NVIM_DIR/ftdetect/"
            cp "$VIM_SYNTAX_DIR/mrr.vim" "$NVIM_DIR/syntax/"
            chown -R "$REAL_USER:$REAL_USER" "$NVIM_DIR" 2>/dev/null || true
            echo -e "  ${GREEN}✓ Neovim syntax dosyası kuruldu${NC}"
        fi
    fi
    
    # Sublime Text
    SUBLIME_DIRS=(
        "$REAL_HOME/.config/sublime-text/Packages/User"
        "$REAL_HOME/.config/sublime-text-3/Packages/User"
    )
    for SUBLIME_DIR in "${SUBLIME_DIRS[@]}"; do
        if [ -d "$(dirname "$SUBLIME_DIR")" ]; then
            echo -e "  ${CYAN}→ Sublime Text tespit edildi${NC}"
            mkdir -p "$SUBLIME_DIR"
            cat > "$SUBLIME_DIR/mrr.sublime-syntax" << 'SUBLIME'
%YAML 1.2
---
name: MRR
file_extensions: [mrr]
scope: source.mrr

contexts:
  main:
    - match: '\b(Fonction|Function|fn|let|mut|const|if|elif|else|for|while|loop|match|return|break|continue|struct|class|trait|impl|pub|unsafe|kernel|exploit|hook|driver)\b'
      scope: keyword.control.mrr
    - match: '\b(i8|i16|i32|i64|u8|u16|u32|u64|f32|f64|str|bool|byte|void)\b'
      scope: storage.type.mrr
    - match: '//.*$'
      scope: comment.line.mrr
    - match: '#.*$'
      scope: comment.line.mrr
    - match: '"[^"]*"'
      scope: string.quoted.double.mrr
    - match: '\b\d+\b'
      scope: constant.numeric.mrr
SUBLIME
            chown -R "$REAL_USER:$REAL_USER" "$SUBLIME_DIR" 2>/dev/null || true
            echo -e "  ${GREEN}✓ Sublime Text syntax dosyası kuruldu${NC}"
            break
        fi
    done
}

# ─────────────────────────────────────────────────────
# Dosya İzinleri
# ─────────────────────────────────────────────────────

set_permissions() {
    echo -e "${BOLD}[6/6] Dosya izinleri ayarlanıyor...${NC}"
    
    chmod -R 755 "$MRR_INSTALL_DIR"
    chmod 755 "$MRR_BIN"
    
    echo -e "  ${GREEN}✓ İzinler ayarlandı${NC}"
}

# ─────────────────────────────────────────────────────
# Ana Akış
# ─────────────────────────────────────────────────────

main() {
    print_banner
    check_root
    check_python
    install_mrr
    create_launcher
    setup_path
    install_editor_extensions
    set_permissions
    
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  MRR v${MRR_VERSION} kurulumu tamamlandı!${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Kullanım:"
    echo "    mrr run hello.mrr          Dosyayı çalıştır"
    echo "    mrr build hello.mrr        .mbuild oluştur"
    echo "    mrr check hello.mrr        Syntax kontrolü"
    echo "    mrr version                Sürüm bilgisi"
    echo ""
    echo -e "  ${YELLOW}NOT: Değişikliklerin etkili olması için terminal'i yeniden açın.${NC}"
    echo ""
}

main "$@"
