"""
Testa o VisitorSemantico construindo as ASTs manualmente,
sem precisar chamar yacc.yacc() (evita o travamento do PLY).
Grava o resultado em resultado_testes.txt
"""
import sys, os

OUTPUT = []

def p(*args, **kwargs):
    line = " ".join(str(a) for a in args)
    OUTPUT.append(line)
    print(line, **kwargs)

# ── Configurar paths ──────────────────────────────────────────────────
raiz = os.path.dirname(os.path.abspath(__file__))
sintatico = os.path.join(raiz, 'codigoPLY', 'SintaticoPLY')
codigo_dir = os.path.join(raiz, 'codigoPLY')
sys.path.insert(0, sintatico)
sys.path.insert(0, codigo_dir)

# ── Importar apenas o que não depende do PLY ──────────────────────────
p("Importando SintaxeAbstrata...")
import SintaxeAbstrata as sa
p("Importando SymbolTable...")
import SymbolTable as st
p("Importando AbstractVisitor...")
import AbstractVisitor
p("Importando VisitorSemantico (classe apenas)...")

# Importa so a classe, sem chamar yacc
# Monkey-patch: substitui yacc.yacc antes do import
import types
fake_yacc_mod = types.ModuleType("ply.yacc")
def fake_yacc(*a, **kw):
    class FakeParser:
        def parse(self, *a, **kw): return None
    return FakeParser()
fake_yacc_mod.yacc = fake_yacc
sys.modules['ply.yacc'] = fake_yacc_mod

# Tambem patch o ley.lex para evitar erro
import ply.lex  # importa o real, so para nao quebrar outras coisas

from VisitorSemantico import VisitorSemantico

p("OK! Imports concluidos.\n")

# ── TESTE 1: Código CORRETO ───────────────────────────────────────────
p("\n" + "#" * 70)
p("  TESTE 1: Código CORRETO (nenhum erro esperado)")
p("  (AST construída manualmente)")
p("#" * 70)

# function soma(a, b) return a + b end
# local x = 10; local y = 20
# local resultado = soma(x, y)
# if x == y then print("Iguais") else print("Diferentes") end
# for i = 1, 10, 2 do print(i) end

arvore1 = sa.Block([
    sa.FunctionDecl(
        sa.String("soma"),
        [sa.String("a"), sa.String("b")],
        sa.Block([sa.Return(sa.BinOp(sa.Var("a"), "+", sa.Var("b")))])
    ),
    sa.Assign(sa.String("x"), sa.Number(10)),
    sa.Assign(sa.String("y"), sa.Number(20)),
    sa.Assign(sa.String("resultado"), sa.FunctionCall(sa.String("soma"), [sa.Var("x"), sa.Var("y")])),
    sa.If(
        sa.BinOp(sa.Var("x"), "==", sa.Var("y")),
        sa.Block([sa.FunctionCall("print", [sa.String("Iguais")])]),
        sa.Block([sa.FunctionCall("print", [sa.String("Diferentes")])]),
        []
    ),
    sa.For(
        sa.String("i"),
        sa.Number(1),
        sa.Number(10),
        sa.Number(2),
        sa.Block([sa.FunctionCall("print", [sa.Var("i")])])
    ),
])

v1 = VisitorSemantico()
arvore1.accept(v1)
v1.relatorio()

# ── TESTE 2: Código COM ERROS ─────────────────────────────────────────
p("\n" + "#" * 70)
p("  TESTE 2: Código COM ERROS (erros devem ser detectados)")
p("  Erros esperados:")
p("    - 'calcular' não foi declarada")
p("    - 'texto + 5' mistura string com número")
p("    - 'y' não foi declarada")
p("#" * 70)

# local x = 10
# local resultado = calcular(x)   -- ERRO: calcular nao declarada
# local texto = "lua"
# local conta = texto + 5          -- AVISO: string + number
# print(y)                         -- ERRO: y nao declarada

arvore2 = sa.Block([
    sa.Assign(sa.String("x"), sa.Number(10)),
    sa.Assign(sa.String("resultado"), sa.FunctionCall(sa.String("calcular"), [sa.Var("x")])),
    sa.Assign(sa.String("texto"), sa.String("lua")),
    sa.Assign(sa.String("conta"), sa.BinOp(sa.Var("texto"), "+", sa.Number(5))),
    sa.FunctionCall("print", [sa.Var("y")]),
])

v2 = VisitorSemantico()
arvore2.accept(v2)
v2.relatorio()

# ── TESTE 3: Escopos ──────────────────────────────────────────────────
p("\n" + "#" * 70)
p("  TESTE 3: Verificação de ESCOPOS")
p("#" * 70)

# local a = 1
# function dobrar(n) return n + n end
# local b = dobrar(a)
# if a == 1 then local c = 100; print(c) end

arvore3 = sa.Block([
    sa.Assign(sa.String("a"), sa.Number(1)),
    sa.FunctionDecl(
        sa.String("dobrar"),
        [sa.String("n")],
        sa.Block([sa.Return(sa.BinOp(sa.Var("n"), "+", sa.Var("n")))])
    ),
    sa.Assign(sa.String("b"), sa.FunctionCall(sa.String("dobrar"), [sa.Var("a")])),
    sa.If(
        sa.BinOp(sa.Var("a"), "==", sa.Number(1)),
        sa.Block([
            sa.Assign(sa.String("c"), sa.Number(100)),
            sa.FunctionCall("print", [sa.Var("c")])
        ]),
        None,
        []
    ),
])

v3 = VisitorSemantico()
arvore3.accept(v3)
v3.relatorio()

# ── TESTE 4: FOR numérico ─────────────────────────────────────────────
p("\n" + "#" * 70)
p("  TESTE 4: Laço FOR numérico (deve passar)")
p("#" * 70)

# for i = 1, 10, 2 do print(i) end

arvore4 = sa.Block([
    sa.For(
        sa.String("i"),
        sa.Number(1),
        sa.Number(10),
        sa.Number(2),
        sa.Block([sa.FunctionCall("print", [sa.Var("i")])])
    ),
])

v4 = VisitorSemantico()
arvore4.accept(v4)
v4.relatorio()

# ── Gravar resultado ──────────────────────────────────────────────────
result_file = os.path.join(raiz, 'resultado_testes.txt')
with open(result_file, 'w', encoding='utf-8') as f:
    f.write("\n".join(OUTPUT))

p("\n\nResultado gravado em:", result_file)
