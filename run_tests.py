import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ply.yacc as yacc
from io import StringIO
from SintaticoPLY.ExpressionLanguageParser import parser
from SintaticoPLY.PrettyPrinter import PrettyPrinter

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title):
    print(f"\n{Colors.HEADER}{'=' * 70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.CYAN}{title.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{'=' * 70}{Colors.END}\n")

def print_section(title):
    print(f"\n{Colors.YELLOW}{'-' * 50}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}>> {title}{Colors.END}")
    print(f"{Colors.YELLOW}{'-' * 50}{Colors.END}")

def print_code(code):
    print(f"{Colors.CYAN}Codigo Lua:{Colors.END}")
    for i, line in enumerate(code.strip().split('\n'), 1):
        print(f"  {Colors.HEADER}{i:3d} |{Colors.END} {line}")

def run_test(name, code, expect_error=False):
    print_section(name)
    print_code(code)
    
    try:
        result = parser.parse(code)
        if expect_error:
            print(f"\n{Colors.RED}[FALHA] Era esperado um erro{Colors.END}")
            return False
        if result is None:
            print(f"\n{Colors.RED}[ERRO] Resultado None{Colors.END}")
            return False
        print(f"\n{Colors.GREEN}[OK] Parse concluido!{Colors.END}")
        print(f"\n{Colors.BOLD}AST:{Colors.END} {result}")
        
        pp = PrettyPrinter()
        regenerated = pp.visit(result)
        print(f"\n{Colors.BOLD}Codigo Regenerado (PrettyPrinter):{Colors.END}")
        print(regenerated)
        return True
    except Exception as e:
        if expect_error:
            print(f"\n{Colors.GREEN}[OK] Erro esperado: {e}{Colors.END}")
            return True
        print(f"\n{Colors.RED}[ERRO] {e}{Colors.END}")
        return False

def main():
    print_header("ANALISADOR SINTATICO LUA - PLY")
    
    tests = [
        ("1. Funcoes", "function soma(a, b)\n    return a + b\nend"),
        ("2. If/Else", "if x > 10 then\n    print(x)\nelse\n    print(0)\nend"),
        ("3. While", "while x < 10 do\n    x = x + 1\nend"),
        ("4. For Numerico", "for i = 1, 10 do\n    print(i)\nend"),
        ("5. For Generico", "for k, v in pairs(t) do\n    print(k)\nend"),
        ("6. Repeat-Until", "repeat\n    x = x + 1\nuntil x >= 10"),
        ("7. Comparacoes", "local r = a ~= b\nlocal s = a <= b"),
        ("8. Logicos", "local x = true and false\nlocal y = not x"),
        ("9. Matematica", "local x = 2 ^ 10\nlocal y = 10 % 3"),
        ("10. Strings", 'local s = "hello" .. " world"\nlocal t = #s'),
        ("11. Break", "while true do\n    break\nend"),
        ("12. ElseIf", "if x > 90 then\n    print(\"A\")\nelseif x > 80 then\n    print(\"B\")\nelse\n    print(\"C\")\nend"),
        ("13. Erro Sintaxe", "local x = = 10", True),
        ("14. End Faltando", "if true then\n    print(1)", True),
    ]
    
    passed = sum(1 for name, code, *err in tests if run_test(name, code, err[0] if err else False))
    total = len(tests)
    
    print_header("RESUMO")
    color = Colors.GREEN if passed == total else Colors.RED
    print(f"  Testes: {passed}/{total}")
    print(f"  {color}Taxa: {passed/total*100:.0f}%{Colors.END}\n")

if __name__ == "__main__":
    main()
