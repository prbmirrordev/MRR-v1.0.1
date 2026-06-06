"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR Analyzer — Compile-Time AI Guard & Static Analysis         ║
║                                                                  ║
║  AST üzerinde gezerek potansiyel performans darboğazlarını      ║
║  (örn. O(N^2) iç içe döngüler) ve güvenlik risklerini tespit    ║
║  eden statik analiz motoru.                                     ║
╚══════════════════════════════════════════════════════════════════╝
"""

from typing import List, Optional
from interpreter.mrr_parser import (
    ASTNode, Program, ForStmt, WhileStmt, DoWhileStmt, FunctionDecl,
    ClassDecl, StructDecl, TraitDecl, ImplDecl, TryCatchStmt, IfStmt,
    MatchStmt, UnsafeBlock, KernelBlock, ExploitDecl, DriverDecl, HookDecl
)

class AnalyzerError(Exception):
    pass

class MRRAnalyzer:
    def __init__(self):
        self.errors = []
        self.warnings = []
        # Döngü derinliğini izlemek için
        self.loop_depth = 0
        self.is_strict = False  # #[ai_guard(strict)] ile açılır

    def analyze(self, program: Program) -> None:
        """Kök dizinden AST'yi analiz eder."""
        for node in program.body:
            self._visit(node)

    def _visit(self, node: ASTNode) -> None:
        if node is None:
            return

        # Ziyaret edilecek tipin metodunu bul
        method_name = f"_visit_{type(node).__name__}"
        visitor = getattr(self, method_name, self._default_visit)
        visitor(node)

    def _default_visit(self, node: ASTNode) -> None:
        # Eğer özel bir ziyaretçi yoksa, alt düğümleri gezin
        if hasattr(node, 'body') and isinstance(node.body, list):
            for child in node.body:
                self._visit(child)
        if hasattr(node, 'then_body') and isinstance(node.then_body, list):
            for child in node.then_body:
                self._visit(child)
        if hasattr(node, 'else_body') and isinstance(node.else_body, list):
            for child in node.else_body:
                self._visit(child)

    def _check_ai_guard(self, decorators: List[str]):
        """ai_guard dekoratörünü kontrol eder."""
        for d in decorators:
            if d.startswith("ai_guard"):
                self.is_strict = "strict" in d
                return True
        return False

    def _visit_FunctionDecl(self, node: FunctionDecl) -> None:
        prev_strict = self.is_strict
        if self._check_ai_guard(node.decorators):
            pass # Eğer özel flag gerekiyorsa burada eklenebilir

        for stmt in node.body:
            self._visit(stmt)

        self.is_strict = prev_strict

    def _visit_ForStmt(self, node: ForStmt) -> None:
        self.loop_depth += 1
        self._check_complexity(node)
        for stmt in node.body:
            self._visit(stmt)
        self.loop_depth -= 1

    def _visit_WhileStmt(self, node: WhileStmt) -> None:
        self.loop_depth += 1
        self._check_complexity(node)
        for stmt in node.body:
            self._visit(stmt)
        self.loop_depth -= 1

    def _visit_DoWhileStmt(self, node: DoWhileStmt) -> None:
        self.loop_depth += 1
        self._check_complexity(node)
        for stmt in node.body:
            self._visit(stmt)
        self.loop_depth -= 1

    def _check_complexity(self, node: ASTNode):
        """Asimptotik karmaşıklık analizi (O(N^2) tespiti)."""
        if self.loop_depth >= 2:
            loc = node.location
            msg = f"AI_GUARD UYARISI: İç içe döngü tespit edildi (O(N^2) veya daha kötü karmaşıklık). ÖNERİ: Algoritmanızı std.collections.HashSet kullanarak O(N) karmaşıklığına optimize ediniz."
            
            if self.is_strict:
                self.errors.append(f"{loc}: {msg}")
                raise AnalyzerError(f"{loc}: {msg}")
            else:
                self.warnings.append(f"{loc}: {msg}")
                # Konsola sarı renkle bas
                print(f"\033[93m{loc}: {msg}\033[0m")
