"""
╔══════════════════════════════════════════════════════════════════╗
║  MRR LLVM Code Generator (Cross-Platform)                      ║
║                                                                  ║
║  MRR Abstract Syntax Tree'yi (AST) okuyup LLVM IR (Intermediate  ║
║  Representation) üreten modül. Üretilen IR daha sonra clang      ║
║  veya llc üzerinden Windows(.exe), Linux(.elf) veya macOS        ║
║  makine koduna derlenir.                                        ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import sys

# llvmlite kütüphanesi Python üzerinden LLVM C++ API'sine erişim sağlar.
try:
    from llvmlite import ir
    from llvmlite import binding as llvm
except ImportError:
    print("[MRR LLVM] ⚠ llvmlite kütüphanesi bulunamadı.")
    print("[MRR LLVM] ⚠ Makine kodu üretimi (compile modu) çalışmayacaktır.")
    ir = None
    llvm = None

try:
    import interpreter.mrr_parser as ast
except ImportError:
    ast = None


class LLVMCodeGen:
    def __init__(self, module_name="mrr_module"):
        if not llvm:
            raise RuntimeError("llvmlite kurulu değil.")
            
        # LLVM altyapısını başlat
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()
        
        # LLVM Modülü ve Builder
        self.module = ir.Module(name=module_name)
        self.module.triple = llvm.get_default_triple()
        self.builder = None
        
        # Tip tanımlamaları (C Types)
        self.i32 = ir.IntType(32)
        self.i64 = ir.IntType(64)
        self.i8  = ir.IntType(8)
        self.f64 = ir.DoubleType()
        self.void = ir.VoidType()
        self.char_ptr = ir.PointerType(self.i8)
        
        # Kapsam (Environment) - Değişkenlerin bellek adresleri
        self.symtab = {}
        
        # printf bildirimi (C Standard Library entegrasyonu)
        printf_ty = ir.FunctionType(self.i32, [self.char_ptr], var_arg=True)
        self.printf = ir.Function(self.module, printf_ty, name="printf")

    def compile(self, program: 'ast.Program') -> str:
        """AST'yi okur ve LLVM IR metnini string olarak döner."""
        print("[LLVM] Makine kodu IR (Intermediate Representation) üretiliyor...")
        
        # main() fonksiyonunu oluştur
        main_ty = ir.FunctionType(self.i32, [])
        main_func = ir.Function(self.module, main_ty, name="main")
        block = main_func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)
        
        for node in program.body:
            self._generate(node)
            
        # main() return 0
        self.builder.ret(ir.Constant(self.i32, 0))
        
        return str(self.module)

    def _generate(self, node):
        if isinstance(node, ast.PrintStmt):
            self._gen_print(node)
        elif isinstance(node, ast.FunctionDecl):
            self._gen_function(node)
        elif isinstance(node, ast.AssignExpr):
            self._gen_assign(node)
        # TODO: Diğer AST tipleri

    def _gen_print(self, node: 'ast.PrintStmt'):
        # Basit PoC: Sadece sabit stringleri basıyoruz
        if isinstance(node.value, ast.LiteralExpr) and isinstance(node.value.value, str):
            text = node.value.value
            if node.newline: text += "\\n"
            
            # String'i global sabit olarak belleğe (data segment) yaz
            fmt = text + "\\0"
            c_fmt = ir.Constant(ir.ArrayType(self.i8, len(fmt)), bytearray(fmt.encode("utf8")))
            global_fmt = ir.GlobalVariable(self.module, c_fmt.type, name=f"str_{id(node)}")
            global_fmt.linkage = 'internal'
            global_fmt.global_constant = True
            global_fmt.initializer = c_fmt
            
            # printf çağrısı
            fmt_ptr = self.builder.bitcast(global_fmt, self.char_ptr)
            self.builder.call(self.printf, [fmt_ptr])

    def _gen_function(self, node: 'ast.FunctionDecl'):
        pass

    def _gen_assign(self, node: 'ast.AssignExpr'):
        pass

    def emit_object_file(self, filename: str):
        """Üretilen IR'ı işletim sistemine uygun nesne dosyasına (.o / .obj) dönüştür."""
        target = llvm.Target.from_default_triple()
        target_machine = target.create_target_machine()
        
        # Optimize the module
        llvm_module = llvm.parse_assembly(str(self.module))
        llvm_module.verify()
        
        obj_data = target_machine.emit_object(llvm_module)
        with open(filename, "wb") as f:
            f.write(obj_data)
        print(f"[LLVM] Object dosyası üretildi: {filename}")
        
def compile_to_native(ast_program, output_file: str):
    """Ana derleme hattı."""
    codegen = LLVMCodeGen()
    ir_code = codegen.compile(ast_program)
    
    # AST'nin karmaşıklaştığı IR kodunu loglayabiliriz
    # print(ir_code)
    
    obj_file = output_file + (".obj" if sys.platform == "win32" else ".o")
    codegen.emit_object_file(obj_file)
    
    # 3. Adım Linker aşaması (Clang/GCC veya LLD kullanılacak)
    print(f"[Linker] {obj_file} makine koduna (executable) bağlanacak...")
    return obj_file
