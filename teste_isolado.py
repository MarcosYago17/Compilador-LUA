"""
Teste isolado do VisitorSemantico — sem depender do PLY.
Usa apenas SintaxeAbstrata, SymbolTable e AbstractVisitor.
"""
import sys, os

raiz = os.path.dirname(os.path.abspath(__file__))
sintatico = os.path.join(raiz, 'codigoPLY', 'SintaticoPLY')
sys.path.insert(0, sintatico)
sys.path.insert(0, os.path.join(raiz, 'codigoPLY'))

# Importa módulos sem dependência do PLY
import SintaxeAbstrata as sa
import SymbolTable as st
import AbstractVisitor

# ─── Classe VisitorSemantico copiada aqui para evitar o import do PLY ───
class VisitorSemantico(AbstractVisitor.AbstractVisitor):
    def __init__(self):
        super().__init__()
        self.erros = []
        self.avisos = []
        st.reset_table()
        self._registrar_builtins()

    def _registrar_builtins(self):
        for nome in ['print', 'type', 'tostring', 'tonumber',
                     'pairs', 'ipairs', 'pcall', 'error',
                     'assert', 'require', 'unpack', 'select',
                     'rawget', 'rawset', 'setmetatable', 'getmetatable']:
            try:
                st.add_function(nome, params=None, return_type=None)
            except Exception:
                pass

    def _erro(self, mensagem):
        self.erros.append(f"[ERRO] {mensagem}")

    def _aviso(self, mensagem):
        self.avisos.append(f"[AVISO] {mensagem}")

    def _extrair_nome(self, node):
        if hasattr(node, 'value'):
            return node.value
        return str(node)

    def visitNumber(self, node):
        return st.NUMBER

    def visitString(self, node):
        return st.STRING

    def visitBoolean(self, node):
        return st.BOOLEAN

    def visitNil(self, node):
        return st.NIL

    def visitVar(self, node):
        if not st.symbol_exists(node.name):
            self._erro(f"Variável '{node.name}' usada sem ter sido declarada")
            return None
        simbolo = st.lookup_symbol(node.name)
        return simbolo[st.TYPE] if simbolo else None

    def visitUnOp(self, node):
        tipo = node.operand.accept(self)
        op = node.op.strip() if isinstance(node.op, str) else node.op
        if op == '-':
            if tipo and tipo != st.NUMBER:
                self._aviso(f"Operador '-' aplicado a tipo '{tipo}' (esperado: number)")
            return st.NUMBER
        elif op == 'not':
            return st.BOOLEAN
        return None

    def visitBinOp(self, node):
        tipo_esq = node.left.accept(self)
        tipo_dir = node.right.accept(self)
        if node.op in ['+', '-', '*', '/']:
            if tipo_esq and tipo_esq not in [st.NUMBER, st.NIL]:
                self._aviso(f"Operador '{node.op}': lado esquerdo é '{tipo_esq}', esperado 'number'")
            if tipo_dir and tipo_dir not in [st.NUMBER, st.NIL]:
                self._aviso(f"Operador '{node.op}': lado direito é '{tipo_dir}', esperado 'number'")
            return st.NUMBER
        elif node.op in ['==', '~=', '<', '>', '<=', '>=']:
            return st.BOOLEAN
        elif node.op in ['and', 'or']:
            return tipo_esq
        return None

    def visitFunctionCall(self, node):
        nome = self._extrair_nome(node.name)
        if not st.symbol_exists(nome):
            self._erro(f"Função '{nome}' chamada sem ter sido declarada")
        else:
            simbolo = st.lookup_symbol(nome)
            if simbolo and simbolo[st.CATEGORY] != st.FUNC:
                self._aviso(f"'{nome}' não é uma função, mas foi chamada como uma")
            if simbolo and simbolo.get(st.PARAMS):
                esperados = len(simbolo[st.PARAMS])
                recebidos = len(node.args)
                if recebidos != esperados:
                    self._aviso(f"Função '{nome}' espera {esperados} argumento(s), recebeu {recebidos}")
        for arg in node.args:
            arg.accept(self)
        return None

    def visitAssign(self, node):
        nome = self._extrair_nome(node.name)
        tipo_exp = node.exp.accept(self)
        if st.symbol_exists(nome):
            simbolo = st.lookup_symbol(nome)
            if simbolo:
                simbolo[st.TYPE] = tipo_exp
        else:
            try:
                st.add_variable(nome, var_type=tipo_exp, is_local=True)
            except Exception as e:
                self._erro(str(e))

    def visitFunctionDecl(self, node):
        nome = self._extrair_nome(node.name)
        nomes_params = [self._extrair_nome(p) for p in node.params]
        try:
            st.add_function(nome, params=nomes_params, return_type=None)
        except Exception as e:
            self._erro(str(e))
        st.enter_scope()
        for param in nomes_params:
            try:
                st.add_variable(param, var_type=None, is_local=True)
            except Exception as e:
                self._erro(str(e))
        node.body.accept(self)
        st.exit_scope()

    def visitFor(self, node):
        st.enter_scope()
        nome_var = self._extrair_nome(node.var)
        try:
            st.add_variable(nome_var, var_type=st.NUMBER, is_local=True)
        except Exception as e:
            self._erro(str(e))
        tipo_ini = node.start.accept(self)
        if tipo_ini and tipo_ini != st.NUMBER:
            self._erro(f"For: valor inicial deve ser número, recebeu '{tipo_ini}'")
        tipo_fim = node.end.accept(self)
        if tipo_fim and tipo_fim != st.NUMBER:
            self._erro(f"For: valor final deve ser número, recebeu '{tipo_fim}'")
        if node.step:
            tipo_passo = node.step.accept(self)
            if tipo_passo and tipo_passo != st.NUMBER:
                self._erro(f"For: passo deve ser número, recebeu '{tipo_passo}'")
        node.body.accept(self)
        st.exit_scope()

    def visitReturn(self, node):
        if node.exp:
            return node.exp.accept(self)
        return st.NIL

    def visitIf(self, node):
        node.condition.accept(self)
        st.enter_scope()
        node.then_body.accept(self)
        st.exit_scope()
        if node.elseif_list:
            for ei_cond, ei_body in node.elseif_list:
                ei_cond.accept(self)
                st.enter_scope()
                ei_body.accept(self)
                st.exit_scope()
        if node.else_body:
            st.enter_scope()
            node.else_body.accept(self)
            st.exit_scope()

    def visitBlock(self, node):
        if node.statements:
            for stmt in node.statements:
                stmt.accept(self)

    def relatorio(self):
        print("\n" + "=" * 70)
        print("           RELATÓRIO DA ANÁLISE SEMÂNTICA")
        print("=" * 70)
        if not self.erros and not self.avisos:
            print("\n  Nenhum problema semântico encontrado!\n")
        if self.erros:
            print(f"\n  {len(self.erros)} ERRO(S) SEMÂNTICO(S):\n")
            for i, erro in enumerate(self.erros, 1):
                print(f"    {i}. {erro}")
        if self.avisos:
            print(f"\n  {len(self.avisos)} AVISO(S):\n")
            for i, aviso in enumerate(self.avisos, 1):
                print(f"    {i}. {aviso}")
        print("\n" + "-" * 70)
        print("TABELA DE SÍMBOLOS FINAL:")
        st.print_table()
        sucesso = len(self.erros) == 0
        print("RESULTADO:", "APROVADO (sem erros)" if sucesso else "REPROVADO (erros encontrados)")
        print("=" * 70 + "\n")
        return sucesso


# ═══════════════════════════════════════════════════════════════
#                          TESTES
# ═══════════════════════════════════════════════════════════════

print("=" * 70)
print("     ANÁLISE SEMÂNTICA - Compilador Lua")
print("     Atividade 6 - LFT")
print("=" * 70)

# ── TESTE 1: Código CORRETO ──────────────────────────────────────────
print("\n" + "#" * 70)
print("  TESTE 1: Código CORRETO (nenhum erro esperado)")
print("#" * 70)

arvore1 = sa.Block([
    sa.FunctionDecl(
        sa.String("soma"),
        [sa.String("a"), sa.String("b")],
        sa.Block([sa.Return(sa.BinOp(sa.Var("a"), "+", sa.Var("b")))])
    ),
    sa.Assign(sa.String("x"), sa.Number(10)),
    sa.Assign(sa.String("y"), sa.Number(20)),
    sa.Assign(sa.String("resultado"),
              sa.FunctionCall(sa.String("soma"), [sa.Var("x"), sa.Var("y")])),
    sa.If(
        sa.BinOp(sa.Var("x"), "==", sa.Var("y")),
        sa.Block([sa.FunctionCall("print", [sa.String("Iguais")])]),
        sa.Block([sa.FunctionCall("print", [sa.String("Diferentes")])]),
        []
    ),
    sa.For(
        sa.String("i"), sa.Number(1), sa.Number(10), sa.Number(2),
        sa.Block([sa.FunctionCall("print", [sa.Var("i")])])
    ),
])

v1 = VisitorSemantico()
arvore1.accept(v1)
v1.relatorio()

# ── TESTE 2: Código COM ERROS ────────────────────────────────────────
print("\n" + "#" * 70)
print("  TESTE 2: Código COM ERROS (erros devem ser detectados)")
print("  Erros esperados:")
print("    - 'calcular' não foi declarada")
print("    - 'texto + 5' mistura string com número")
print("    - 'y' não foi declarada")
print("#" * 70)

arvore2 = sa.Block([
    sa.Assign(sa.String("x"), sa.Number(10)),
    sa.Assign(sa.String("resultado"),
              sa.FunctionCall(sa.String("calcular"), [sa.Var("x")])),
    sa.Assign(sa.String("texto"), sa.String("lua")),
    sa.Assign(sa.String("conta"),
              sa.BinOp(sa.Var("texto"), "+", sa.Number(5))),
    sa.FunctionCall("print", [sa.Var("y")]),
])

v2 = VisitorSemantico()
arvore2.accept(v2)
v2.relatorio()

# ── TESTE 3: Escopos ─────────────────────────────────────────────────
print("\n" + "#" * 70)
print("  TESTE 3: Verificação de ESCOPOS")
print("#" * 70)

arvore3 = sa.Block([
    sa.Assign(sa.String("a"), sa.Number(1)),
    sa.FunctionDecl(
        sa.String("dobrar"),
        [sa.String("n")],
        sa.Block([sa.Return(sa.BinOp(sa.Var("n"), "+", sa.Var("n")))])
    ),
    sa.Assign(sa.String("b"),
              sa.FunctionCall(sa.String("dobrar"), [sa.Var("a")])),
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

# ── TESTE 4: FOR numérico ────────────────────────────────────────────
print("\n" + "#" * 70)
print("  TESTE 4: Laço FOR numérico (deve passar)")
print("#" * 70)

arvore4 = sa.Block([
    sa.For(
        sa.String("i"), sa.Number(1), sa.Number(10), sa.Number(2),
        sa.Block([sa.FunctionCall("print", [sa.Var("i")])])
    ),
])

v4 = VisitorSemantico()
arvore4.accept(v4)
v4.relatorio()

print("\n" + "=" * 70)
print("  TODOS OS TESTES CONCLUÍDOS!")
print("=" * 70)
