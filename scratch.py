import sys
sys.path.insert(0, r'c:\Users\efdee\OneDrive\Desktop\mrr')
from interpreter.mrr_lexer import Lexer
from interpreter.mrr_parser import Parser
from interpreter.mrr_evaluator import Evaluator
from interpreter.mrr_ffi import FFIBridge

code = """
add.code "nmap"
let nm = nmap::PortScanner()
"""

tokens = Lexer(code).tokenize()
program = Parser(tokens).parse()

evaluator = Evaluator()
evaluator.ffi_bridge = FFIBridge()
try:
    evaluator.execute(program)
    print("Eval OK. nm object type:", type(evaluator.global_env.get("nm")))
except Exception as e:
    print("Eval failed:", e)
