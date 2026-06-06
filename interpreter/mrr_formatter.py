"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Formatter — Otomatik Kod Biçimlendirici                    ║
║                                                                  ║
║  MRR kaynak kodunu tutarlı bir formata dönüştürür.              ║
║  Prettier/gofmt benzeri otomatik biçimlendirme.                 ║
║                                                                  ║
║  Kurallar:                                                       ║
║    - 4 boşluk girinti (tab → space)                              ║
║    - Operatörler etrafında boşluk                                ║
║    - Virgülden sonra boşluk                                      ║
║    - Fonksiyon öncesi 1 boş satır                                ║
║    - Class/struct öncesi 2 boş satır                             ║
║    - Trailing whitespace temizleme                               ║
║    - Max satır uzunluğu: 120 karakter                            ║
╚══════════════════════════════════════════════════════════════════╝
"""

from __future__ import annotations
import re
import sys
from typing import List, Optional, Tuple
from pathlib import Path


class FormatterConfig:
    """Formatter yapılandırması."""
    def __init__(self):
        self.indent_size: int = 4
        self.use_tabs: bool = False
        self.max_line_length: int = 120
        self.insert_final_newline: bool = True
        self.trim_trailing_whitespace: bool = True
        self.space_around_operators: bool = True
        self.space_after_comma: bool = True
        self.blank_lines_before_function: int = 1
        self.blank_lines_before_class: int = 2
        self.sort_imports: bool = True
        self.align_assignments: bool = False


class MRRFormatter:
    """
    MRR Kod Biçimlendirici.
    
    Kaynak kodu alır, biçimlendirilmiş halini döndürür.
    """

    # Fonksiyon/Sınıf başlatan anahtar kelimeler
    BLOCK_STARTERS = {
        'Fonction.create', 'Function.create', 'fn', 'class', 'struct',
        'enum', 'trait', 'impl', 'exploit', 'driver', 'hook', 'kernel',
        'module',
    }
    
    CONTROL_KEYWORDS = {
        'if', 'elif', 'otherwise', 'for', 'while', 'loop', 'match',
        'try', 'catch', 'finally', 'do', 'unsafe',
    }

    # Operatörler — etrafına boşluk konulacak
    BINARY_OPERATORS = re.compile(
        r'(?<!=)(?<!!)'             # Başına != veya ! gelmemeli
        r'(?<![<>])'                # <<, >> koruması
        r'('
        r'\+(?!=)|'                 # + (ama += değil)
        r'-(?!=|>)|'                # - (ama -= ve -> değil)
        r'\*(?!=|\*)|'              # * (ama *= ve ** değil)
        r'/(?!=)|'                  # / (ama /= değil)
        r'%(?!=)|'                  # % (ama %= değil)
        r'==|!=|<=|>=|'             # Karşılaştırma
        r'&&|\|\||'                 # Mantıksal
        r'(?<!\.)\.\.(?!\.)'        # .. (range, ama ... değil)
        r')'
        r'(?!=)'                    # Sonuna = gelmemeli
    )

    def __init__(self, config: Optional[FormatterConfig] = None):
        self.config = config or FormatterConfig()
        self._indent_char = '\t' if self.config.use_tabs else ' ' * self.config.indent_size

    def format_source(self, source: str) -> str:
        """Kaynak kodu biçimlendir ve döndür."""
        lines = source.split('\n')
        
        # Faz 1: Temel temizlik
        lines = self._trim_trailing_whitespace(lines)
        lines = self._normalize_tabs(lines)
        
        # Faz 2: Boşluk düzenleme
        lines = self._fix_operator_spacing(lines)
        lines = self._fix_comma_spacing(lines)
        lines = self._fix_colon_spacing(lines)
        
        # Faz 3: Boş satır düzenleme
        lines = self._fix_blank_lines(lines)
        lines = self._remove_excessive_blank_lines(lines)
        
        # Faz 4: Import sıralama
        if self.config.sort_imports:
            lines = self._sort_imports(lines)
        
        # Faz 5: Son satır
        result = '\n'.join(lines)
        if self.config.insert_final_newline:
            if not result.endswith('\n'):
                result += '\n'
        
        return result

    def format_file(self, filepath: str, write: bool = False) -> str:
        """Dosyayı biçimlendir. write=True ise dosyaya yaz."""
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Dosya bulunamadı: {filepath}")
        if path.suffix != '.mrr':
            raise ValueError(f"Sadece .mrr dosyaları biçimlendirilebilir: {filepath}")
        
        source = path.read_text(encoding='utf-8')
        formatted = self.format_source(source)
        
        if write:
            path.write_text(formatted, encoding='utf-8')
        
        return formatted

    def check_format(self, source: str) -> Tuple[bool, List[str]]:
        """Kodun formatlanmış olup olmadığını kontrol et."""
        formatted = self.format_source(source)
        if source == formatted:
            return True, []
        
        # Farklılıkları bul
        diffs = []
        orig_lines = source.split('\n')
        fmt_lines = formatted.split('\n')
        
        max_lines = max(len(orig_lines), len(fmt_lines))
        for i in range(max_lines):
            orig = orig_lines[i] if i < len(orig_lines) else '<missing>'
            fmt = fmt_lines[i] if i < len(fmt_lines) else '<missing>'
            if orig != fmt:
                diffs.append(f"  Satır {i + 1}: '{orig.strip()}' → '{fmt.strip()}'")
        
        return False, diffs

    # ─────────────────────────────────────────────────────
    # İç Yardımcı Metodlar
    # ─────────────────────────────────────────────────────

    def _trim_trailing_whitespace(self, lines: List[str]) -> List[str]:
        """Satır sonu boşluklarını temizle."""
        if not self.config.trim_trailing_whitespace:
            return lines
        return [line.rstrip() for line in lines]

    def _normalize_tabs(self, lines: List[str]) -> List[str]:
        """Tab'ları boşluğa çevir (veya tersi)."""
        if self.config.use_tabs:
            return lines
        result = []
        for line in lines:
            # Satır başındaki tab'ları boşluğa çevir
            leading = ''
            rest = line
            while rest.startswith('\t'):
                leading += ' ' * self.config.indent_size
                rest = rest[1:]
            result.append(leading + rest)
        return result

    def _is_in_string(self, line: str, pos: int) -> bool:
        """Verilen pozisyonun string literal içinde olup olmadığını kontrol et."""
        in_string = False
        string_char = None
        i = 0
        while i < pos and i < len(line):
            c = line[i]
            if c == '\\' and in_string:
                i += 2  # Escape karakterini atla
                continue
            if c in ('"', "'") and not in_string:
                in_string = True
                string_char = c
            elif c == string_char and in_string:
                in_string = False
                string_char = None
            i += 1
        return in_string

    def _is_comment_line(self, line: str) -> bool:
        """Satırın yorum satırı olup olmadığını kontrol et."""
        stripped = line.strip()
        return stripped.startswith('//') or stripped.startswith('#') or stripped.startswith('/*')

    def _fix_operator_spacing(self, lines: List[str]) -> List[str]:
        """Operatörler etrafına boşluk ekle."""
        if not self.config.space_around_operators:
            return lines
        
        result = []
        for line in lines:
            if self._is_comment_line(line):
                result.append(line)
                continue
            
            # String dışındaki kısımları bul ve düzelt
            new_line = self._fix_spacing_outside_strings(line)
            result.append(new_line)
        return result

    def _fix_spacing_outside_strings(self, line: str) -> str:
        """String'lerin dışındaki operatör boşluklarını düzelt."""
        # Basit yaklaşım: string'leri koru, aradaki kısımları düzelt
        parts = []
        in_string = False
        string_char = None
        current = []
        i = 0
        
        while i < len(line):
            c = line[i]
            
            if c == '\\' and in_string and i + 1 < len(line):
                current.append(c)
                current.append(line[i + 1])
                i += 2
                continue
            
            if c in ('"', "'") and not in_string:
                # String dışındaki kısmı düzelt
                code_part = ''.join(current)
                parts.append(self._apply_operator_spacing(code_part))
                current = [c]
                in_string = True
                string_char = c
                i += 1
                continue
            
            if c == string_char and in_string:
                current.append(c)
                parts.append(''.join(current))
                current = []
                in_string = False
                string_char = None
                i += 1
                continue
            
            current.append(c)
            i += 1
        
        # Son kısmı ekle
        if current:
            code_part = ''.join(current)
            if in_string:
                parts.append(code_part)
            else:
                parts.append(self._apply_operator_spacing(code_part))
        
        return ''.join(parts)

    def _apply_operator_spacing(self, code: str) -> str:
        """Kod parçasındaki operatörlere boşluk ekle."""
        # Atama operatörleri
        # += -= *= /= %= **=  — bunların etrafında boşluk olmalı
        code = re.sub(r'\s*(\+=|-=|\*=|/=|%=|&=|\|=|\^=|<<=|>>=|\*\*=)\s*', r' \1 ', code)
        
        # Tek = (ama == değil ve => ve <= değil)
        code = re.sub(r'(?<![=!<>])=(?!=|>)', r' = ', code)
        
        # == !=
        code = re.sub(r'\s*(==|!=)\s*', r' \1 ', code)
        
        # <= >=
        code = re.sub(r'\s*(<=|>=)\s*', r' \1 ', code)
        
        # && ||
        code = re.sub(r'\s*(&&|\|\|)\s*', r' \1 ', code)
        
        # Çift boşlukları temizle
        code = re.sub(r'  +', ' ', code)
        
        return code

    def _fix_comma_spacing(self, lines: List[str]) -> List[str]:
        """Virgülden sonra boşluk ekle."""
        if not self.config.space_after_comma:
            return lines
        
        result = []
        for line in lines:
            if self._is_comment_line(line):
                result.append(line)
                continue
            # Virgülden sonra boşluk yoksa ekle (string dışında)
            new_line = re.sub(r',(?!\s)', ', ', line)
            result.append(new_line)
        return result

    def _fix_colon_spacing(self, lines: List[str]) -> List[str]:
        """Tip anotasyonu iki noktalardan sonra boşluk ekle."""
        result = []
        for line in lines:
            if self._is_comment_line(line):
                result.append(line)
                continue
            # Dict/type annotation : den sonra boşluk
            # Ama :: scope operatörünü bozma
            result.append(line)
        return result

    def _fix_blank_lines(self, lines: List[str]) -> List[str]:
        """Fonksiyon ve sınıf tanımlarından önce uygun boş satır ekle."""
        result = []
        prev_was_blank = False
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Fonksiyon tanımı öncesi
            if any(stripped.startswith(kw) for kw in ('fn ', 'Fonction.create', 'Function.create')):
                if i > 0 and result and result[-1].strip() != '' and not result[-1].strip().startswith('//'):
                    # Gerekli boş satır sayısını kontrol et
                    blanks_before = 0
                    j = len(result) - 1
                    while j >= 0 and result[j].strip() == '':
                        blanks_before += 1
                        j -= 1
                    
                    needed = self.config.blank_lines_before_function
                    for _ in range(needed - blanks_before):
                        result.append('')
            
            # Class/Struct tanımı öncesi
            if any(stripped.startswith(kw) for kw in ('class ', 'struct ', 'enum ', 'trait ')):
                if i > 0 and result and result[-1].strip() != '':
                    blanks_before = 0
                    j = len(result) - 1
                    while j >= 0 and result[j].strip() == '':
                        blanks_before += 1
                        j -= 1
                    
                    needed = self.config.blank_lines_before_class
                    for _ in range(needed - blanks_before):
                        result.append('')
            
            result.append(line)
        
        return result

    def _remove_excessive_blank_lines(self, lines: List[str]) -> List[str]:
        """Ardışık 3+ boş satırı 2'ye indir."""
        result = []
        blank_count = 0
        
        for line in lines:
            if line.strip() == '':
                blank_count += 1
                if blank_count <= 2:
                    result.append(line)
            else:
                blank_count = 0
                result.append(line)
        
        # Dosya başındaki boş satırları kaldır
        while result and result[0].strip() == '':
            result.pop(0)
        
        # Dosya sonundaki fazla boş satırları kaldır
        while len(result) > 1 and result[-1].strip() == '' and result[-2].strip() == '':
            result.pop()
        
        return result

    def _sort_imports(self, lines: List[str]) -> List[str]:
        """add.code satırlarını sırala."""
        # Import bloğunu bul
        import_lines = []
        other_lines = []
        import_section_end = 0
        in_import_section = True
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if in_import_section and stripped.startswith('add.code'):
                import_lines.append(line)
                import_section_end = i
            elif in_import_section and stripped == '':
                if import_lines:
                    import_lines.append(line)  # Import'lar arasındaki boş satır
                else:
                    other_lines.append(line)
            elif in_import_section and (stripped.startswith('//') or stripped.startswith('///')):
                if import_lines:
                    import_lines.append(line)
                else:
                    other_lines.append(line)
            else:
                in_import_section = False
                other_lines.append(line)
        
        if not import_lines:
            return lines
        
        # Sadece add.code satırlarını sırala
        actual_imports = [l for l in import_lines if l.strip().startswith('add.code')]
        non_imports = [l for l in import_lines if not l.strip().startswith('add.code')]
        
        actual_imports.sort(key=lambda x: x.strip().lower())
        
        return non_imports + actual_imports + [''] + other_lines


def format_file_cli(filepath: str, check_only: bool = False, 
                     write: bool = True) -> int:
    """CLI'dan çağrılan formatlama fonksiyonu."""
    formatter = MRRFormatter()
    
    try:
        source = Path(filepath).read_text(encoding='utf-8')
    except FileNotFoundError:
        print(f"[HATA] Dosya bulunamadı: {filepath}")
        return 1
    
    if check_only:
        is_formatted, diffs = formatter.check_format(source)
        if is_formatted:
            print(f"✓ {filepath} — zaten formatlanmış")
            return 0
        else:
            print(f"✗ {filepath} — format farkları bulundu:")
            for d in diffs[:10]:
                print(d)
            if len(diffs) > 10:
                print(f"  ... ve {len(diffs) - 10} fark daha")
            return 1
    
    formatted = formatter.format_source(source)
    
    if source == formatted:
        print(f"✓ {filepath} — değişiklik yok")
        return 0
    
    if write:
        Path(filepath).write_text(formatted, encoding='utf-8')
        print(f"✓ {filepath} — formatlandı")
    else:
        # stdout'a yaz
        print(formatted)
    
    return 0
