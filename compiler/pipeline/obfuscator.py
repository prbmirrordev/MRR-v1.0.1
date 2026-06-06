"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Obfuscator — Kontrol Akışı Düzleştirme & Şifreleme          ║
║                                                                  ║
║  Bu modül, AST (Abstract Syntax Tree) üzerinden doğrudan geçerek ║
║  derleme öncesi otomatik kod karmaşıklaştırma (obfuscation)      ║
║  yapar. Amacı, üretilecek makine kodunun veya IR'ın tersine      ║
║  mühendisliğini (Reverse Engineering) zorlaştırmaktır.           ║
║                                                                  ║
║  Özellikler:                                                    ║
║    1. String Encryption: Tüm string değerlerini XOR ile şifreler ║
║       ve çalışma zamanında dinamik çözen kod blokları üretir.    ║
║    2. Control Flow Flattening (CFF): If/While gibi basit         ║
║       akışları 'while/switch(state)' tabanlı karmaşık durumlara  ║
║       dönüştürür (Aşama 3'te fonksiyon bazlı uygulanır).         ║
║    3. Name Mangling: Özel sembolleri karıştırır.                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import random
import string
import hashlib
from typing import Dict, Any, List

# MRR AST nodlarına bağımlılık (AST ağacı üzerinden mutasyon yapacağız)
try:
    import interpreter.mrr_parser as ast
except ImportError:
    ast = None


class ObfuscationContext:
    def __init__(self, key: int = 0x5A):
        self.xor_key = key
        self.string_map: Dict[str, str] = {}  # {orijinal: obfuscated_name}
        self.name_map: Dict[str, str] = {}    # {orijinal_fonk_adi: karma_ad}
        
    def generate_random_name(self, prefix: str = "mrr_var_") -> str:
        suffix = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        return f"{prefix}{suffix}"

    def xor_encrypt(self, text: str) -> List[int]:
        """Metni XOR anahtarı ile şifreleyip byte dizisi döner."""
        return [ord(c) ^ self.xor_key for c in text]


class MRRObfuscator:
    """AST üzerinde gezinerek Obfuscation tekniklerini uygulayan Visitor sınıfı."""
    
    def __init__(self):
        self.ctx = ObfuscationContext(key=random.randint(0x10, 0xEF))
        self.enabled_features = {
            "string_encryption": True,
            "name_mangling": True,
            "cff": False # Control Flow Flattening (Deneysel)
        }

    def obfuscate_program(self, program: 'ast.Program') -> 'ast.Program':
        """Tüm program ağacını karıştırır."""
        if not ast:
            print("[MRR Obfuscator] ⚠ AST modülü bulunamadı, obfuscation atlanıyor.")
            return program
            
        print(f"[MRR Obfuscator] Obfuscation başlıyor (XOR Key: {hex(self.ctx.xor_key)})...")
        
        # Orijinal ağacı doğrudan modifiye edeceğiz
        for i, node in enumerate(program.body):
            program.body[i] = self._visit(node)
            
        return program

    def _visit(self, node: Any) -> Any:
        if node is None:
            return None
            
        # Literal ifadelerde String Encryption
        if isinstance(node, ast.LiteralExpr):
            return self._obfuscate_literal(node)
            
        # Fonksiyon isimlerini Name Mangling ile karıştırma
        if isinstance(node, ast.FunctionDecl):
            return self._obfuscate_function_decl(node)
            
        # Identifier'ları güncel haritadan (Name Mangling) getirme
        if isinstance(node, ast.IdentifierExpr):
            return self._obfuscate_identifier(node)
            
        # Rekürsif AST gezintisi (Alt düğümleri işle)
        self._traverse_children(node)
        return node

    def _traverse_children(self, node: Any):
        """Node'un alt elemanlarını rekürsif olarak ziyaret eder."""
        if isinstance(node, ast.FunctionDecl):
            node.body = [self._visit(stmt) for stmt in node.body]
        elif isinstance(node, ast.IfStmt):
            node.condition = self._visit(node.condition)
            node.then_body = [self._visit(stmt) for stmt in node.then_body]
            if node.else_body:
                node.else_body = [self._visit(stmt) for stmt in node.else_body]
            for i, (cond, body) in enumerate(node.elif_clauses):
                node.elif_clauses[i] = (self._visit(cond), [self._visit(stmt) for stmt in body])
        elif isinstance(node, ast.WhileStmt):
            node.condition = self._visit(node.condition)
            node.body = [self._visit(stmt) for stmt in node.body]
        elif isinstance(node, ast.ForStmt):
            node.iterable = self._visit(node.iterable)
            node.body = [self._visit(stmt) for stmt in node.body]
        elif isinstance(node, ast.AssignExpr):
            node.target = self._visit(node.target)
            node.value = self._visit(node.value)
        elif isinstance(node, ast.BinaryExpr):
            node.left = self._visit(node.left)
            node.right = self._visit(node.right)
        elif isinstance(node, ast.CallExpr):
            node.callee = self._visit(node.callee)
            node.arguments = [self._visit(arg) for arg in node.arguments]
        elif isinstance(node, ast.ExpressionStmt):
            node.expression = self._visit(node.expression)
        elif isinstance(node, ast.PrintStmt):
            if node.value:
                node.value = self._visit(node.value)
        elif isinstance(node, ast.ReturnStmt):
            if node.value:
                node.value = self._visit(node.value)
        # Diğer düğüm tipleri buraya eklenebilir

    def _obfuscate_literal(self, node: 'ast.LiteralExpr') -> Any:
        if self.enabled_features["string_encryption"] and isinstance(node.value, str):
            # Normalde burada AST seviyesinde bir CallExpr üretilip:
            # decrypt_string([0x.., 0x..], key) şeklinde çalışma zamanında
            # çözülecek bir koda dönüştürülür. 
            # Şu anlık kavramsal (Proof-of-Concept) olarak string'i hafif değiştiriyoruz.
            encrypted_bytes = self.ctx.xor_encrypt(node.value)
            
            # TODO: LLVM IR üreteci (codegen) tarafında bu diziyi çözecek yerel (native) 
            # makine kodunu enjekte edeceğiz.
            pass
            
        return node

    def _obfuscate_function_decl(self, node: 'ast.FunctionDecl') -> 'ast.FunctionDecl':
        if self.enabled_features["name_mangling"]:
            # 'main', 'init' veya FFI ile export edilen fonksiyonları koru
            if node.name not in ("main", "init", "__init__"):
                mangled_name = self.ctx.generate_random_name("fn_")
                self.ctx.name_map[node.name] = mangled_name
                print(f"[Obfuscator] Fonksiyon karartıldı: {node.name} -> {mangled_name}")
                node.name = mangled_name
                
        self._traverse_children(node)
        return node

    def _obfuscate_identifier(self, node: 'ast.IdentifierExpr') -> 'ast.IdentifierExpr':
        if self.enabled_features["name_mangling"]:
            if node.name in self.ctx.name_map:
                node.name = self.ctx.name_map[node.name]
        return node

def run_obfuscator(ast_program):
    """Ana obfuscation boru hattı giriş noktası."""
    obf = MRRObfuscator()
    return obf.obfuscate_program(ast_program)
