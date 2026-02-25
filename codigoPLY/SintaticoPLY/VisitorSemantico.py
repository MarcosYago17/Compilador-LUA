import os
import sys

import ply.yacc as yacc

# Ajuste de caminho para encontrar os outros arquivos.
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if raiz not in sys.path:
    sys.path.insert(0, raiz)

_TABDIR = raiz  # codigoPLY (tem parsetab.py valido)


def _criar_parser():
    """Carrega o parser do parsetab.py existente sem reconstruir."""
    if _TABDIR not in sys.path:
        sys.path.insert(0, _TABDIR)
    return yacc.yacc(
        debug=False,
        write_tables=False,
        tabmodule="parsetab",
        outputdir=_TABDIR,
    )


try:
    from . import SintaxeAbstrata as a
    from . import AbstractVisitor
    from . import SymbolTable as st
except ImportError:
    import SintaxeAbstrata as a
    import AbstractVisitor
    import SymbolTable as st

from ExpressionLanguageParser import *  # noqa: F401,F403


class VisitorSemantico(AbstractVisitor.AbstractVisitor):
    def __init__(self):
        super().__init__()
        self.erros = []
        self.avisos = []
        st.reset_table()
        self._registrar_builtins()

    def _registrar_builtins(self):
        for nome in [
            "print",
            "type",
            "tostring",
            "tonumber",
            "pairs",
            "ipairs",
            "pcall",
            "error",
            "assert",
            "require",
            "unpack",
            "select",
            "rawget",
            "rawset",
            "setmetatable",
            "getmetatable",
        ]:
            try:
                st.add_function(nome, params=None, return_type=None)
            except Exception:
                pass

    def _erro(self, mensagem):
        self.erros.append(f"[ERRO] {mensagem}")

    def _aviso(self, mensagem):
        self.avisos.append(f"[AVISO] {mensagem}")

    def _extrair_nome(self, node):
        if hasattr(node, "value"):
            return node.value
        return str(node)

    def _validar_condicao_booleana(self, tipo, contexto):
        # Se nao conseguimos inferir o tipo, nao acusa erro.
        if tipo is None:
            return
        if tipo != st.BOOLEAN:
            self._erro(
                f"Condicao de {contexto} deve ser boolean, mas recebeu '{tipo}'"
            )

    # ==============================================
    #          EXPRESSOES
    # ==============================================

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
            self._erro(f"Variavel '{node.name}' usada sem ter sido declarada")
            return None
        simbolo = st.lookup_symbol(node.name)
        return simbolo[st.TYPE] if simbolo else None

    def visitUnOp(self, node):
        tipo = node.operand.accept(self)
        op = node.op.strip() if isinstance(node.op, str) else node.op

        if op == "-":
            if tipo and tipo != st.NUMBER:
                self._aviso(
                    f"Operador '-' aplicado a tipo '{tipo}' (esperado: number)"
                )
            return st.NUMBER

        if op == "not":
            return st.BOOLEAN

        return None

    def visitBinOp(self, node):
        tipo_esq = node.left.accept(self)
        tipo_dir = node.right.accept(self)
        op = node.op

        if op in ["+", "-", "*", "/"]:
            if tipo_esq and tipo_esq not in [st.NUMBER, st.NIL]:
                self._aviso(
                    f"Operador '{op}': lado esquerdo e '{tipo_esq}', esperado 'number'"
                )
            if tipo_dir and tipo_dir not in [st.NUMBER, st.NIL]:
                self._aviso(
                    f"Operador '{op}': lado direito e '{tipo_dir}', esperado 'number'"
                )
            return st.NUMBER

        if op in ["==", "~=", "<", ">", "<=", ">="]:
            return st.BOOLEAN

        if op in ["and", "or"]:
            if tipo_esq == st.BOOLEAN and tipo_dir == st.BOOLEAN:
                return st.BOOLEAN
            return None

        return None

    def visitFunctionCall(self, node):
        nome = self._extrair_nome(node.name)

        if not st.symbol_exists(nome):
            self._erro(f"Funcao '{nome}' chamada sem ter sido declarada")
        else:
            simbolo = st.lookup_symbol(nome)
            if simbolo and simbolo[st.CATEGORY] != st.FUNC:
                self._erro(f"'{nome}' nao e uma funcao, mas foi chamada como uma")

            if simbolo and simbolo.get(st.PARAMS):
                esperados = len(simbolo[st.PARAMS])
                recebidos = len(node.args)
                if recebidos != esperados:
                    self._erro(
                        f"Funcao '{nome}' espera {esperados} argumento(s), recebeu {recebidos}"
                    )

        for arg in node.args:
            arg.accept(self)

        return None

    # ==============================================
    #          COMANDOS
    # ==============================================

    def visitAssign(self, node):
        nome = self._extrair_nome(node.name)
        tipo_exp = node.exp.accept(self)
        is_local = getattr(node, "is_local", False)

        if is_local:
            try:
                st.add_variable(nome, var_type=tipo_exp, is_local=True)
            except Exception as exc:
                self._erro(str(exc))
            return

        # Atribuicao sem local: atualiza se existir, senao cria global implicita.
        if st.symbol_exists(nome):
            simbolo = st.lookup_symbol(nome)
            if simbolo:
                simbolo[st.TYPE] = tipo_exp
        else:
            try:
                st.add_variable(nome, var_type=tipo_exp, is_local=False)
            except Exception as exc:
                self._erro(str(exc))

    def visitFunctionDecl(self, node):
        nome = self._extrair_nome(node.name)
        nomes_params = [self._extrair_nome(p) for p in node.params]

        try:
            st.add_function(nome, params=nomes_params, return_type=None)
        except Exception as exc:
            self._erro(str(exc))

        st.enter_scope()
        for param in nomes_params:
            try:
                st.add_variable(param, var_type=None, is_local=True)
            except Exception as exc:
                self._erro(str(exc))

        node.body.accept(self)
        st.exit_scope()

    def visitFor(self, node):
        st.enter_scope()
        nome_var = self._extrair_nome(node.var)
        try:
            st.add_variable(nome_var, var_type=st.NUMBER, is_local=True)
        except Exception as exc:
            self._erro(str(exc))

        tipo_ini = node.start.accept(self)
        if tipo_ini and tipo_ini != st.NUMBER:
            self._erro(
                f"For: valor inicial deve ser numero, recebeu '{tipo_ini}'"
            )

        tipo_fim = node.end.accept(self)
        if tipo_fim and tipo_fim != st.NUMBER:
            self._erro(f"For: valor final deve ser numero, recebeu '{tipo_fim}'")

        if node.step:
            tipo_passo = node.step.accept(self)
            if tipo_passo and tipo_passo != st.NUMBER:
                self._erro(f"For: passo deve ser numero, recebeu '{tipo_passo}'")

        node.body.accept(self)
        st.exit_scope()

    def visitWhile(self, node):
        tipo_cond = node.condition.accept(self)
        self._validar_condicao_booleana(tipo_cond, "while")

        st.enter_scope()
        node.body.accept(self)
        st.exit_scope()

    def visitReturn(self, node):
        if node.exp:
            return node.exp.accept(self)
        return st.NIL

    def visitIf(self, node):
        tipo_cond = node.condition.accept(self)
        self._validar_condicao_booleana(tipo_cond, "if")

        st.enter_scope()
        node.then_body.accept(self)
        st.exit_scope()

        for item in node.elseif_list or []:
            if isinstance(item, tuple) and len(item) == 2:
                cond, body = item
            else:
                cond = getattr(item, "condition", None)
                body = getattr(item, "then_body", None)
            if cond is None or body is None:
                continue
            tipo_elseif = cond.accept(self)
            self._validar_condicao_booleana(tipo_elseif, "elseif")
            st.enter_scope()
            body.accept(self)
            st.exit_scope()

        if node.else_body:
            st.enter_scope()
            node.else_body.accept(self)
            st.exit_scope()

    def visitBlock(self, node):
        for stmt in node.statements or []:
            stmt.accept(self)

    # ==============================================
    #              RELATORIO FINAL
    # ==============================================

    def relatorio(self):
        print("\n" + "=" * 70)
        print("           RELATORIO DA ANALISE SEMANTICA")
        print("=" * 70)

        if not self.erros and not self.avisos:
            print("\n  Nenhum problema semantico encontrado!\n")

        if self.erros:
            print(f"\n  {len(self.erros)} ERRO(S) SEMANTICO(S):\n")
            for i, erro in enumerate(self.erros, 1):
                print(f"    {i}. {erro}")

        if self.avisos:
            print(f"\n  {len(self.avisos)} AVISO(S):\n")
            for i, aviso in enumerate(self.avisos, 1):
                print(f"    {i}. {aviso}")

        print("\n" + "-" * 70)
        print("TABELA DE SIMBOLOS FINAL:")
        st.print_table()

        sucesso = len(self.erros) == 0
        msg = "APROVADO (sem erros)" if sucesso else "REPROVADO (erros encontrados)"
        print("RESULTADO:", msg)
        print("=" * 70 + "\n")
        return sucesso


def _executar_teste(codigo, titulo, observacoes=None):
    print("\n" + "#" * 70)
    print(f"  {titulo}")
    if observacoes:
        for linha in observacoes:
            print(f"  {linha}")
    print("#" * 70)

    parser = _criar_parser()
    try:
        arvore = parser.parse(codigo)
    except SyntaxError:
        print("Erro no parsing!")
        return

    if arvore:
        visitor = VisitorSemantico()
        arvore.accept(visitor)
        visitor.relatorio()
    else:
        print("Erro no parsing!")


def teste1_codigo_correto():
    codigo = """
    function soma(a, b)
        return a + b
    end

    local x = 10
    local y = 20
    local resultado = soma(x, y)

    if x == y then
        print("Iguais")
    else
        print("Diferentes")
    end

    for i = 1, 10, 2 do
        print(i)
    end
    """
    _executar_teste(
        codigo,
        "TESTE 1: Codigo CORRETO (nenhum erro esperado)",
    )


def teste2_codigo_com_erros():
    codigo = """
    local x = 10

    local resultado = calcular(x)
    local texto = "lua"
    local conta = texto + 5
    print(y)
    """
    _executar_teste(
        codigo,
        "TESTE 2: Codigo COM ERROS (erros devem ser detectados)",
        observacoes=[
            "Erros esperados:",
            "- 'calcular' nao foi declarada",
            "- 'texto + 5' mistura string com numero",
            "- 'y' nao foi declarada",
        ],
    )


def teste3_escopos():
    codigo = """
    local a = 1

    function dobrar(n)
        return n + n
    end

    local b = dobrar(a)

    if a == 1 then
        local c = 100
        print(c)
    end
    """
    _executar_teste(codigo, "TESTE 3: Verificacao de ESCOPOS")


def teste4_for_com_erro():
    codigo = """
    for i = 1, 10, 2 do
        print(i)
    end
    """
    _executar_teste(codigo, "TESTE 4: Laco FOR numerico (deve passar)")


if __name__ == "__main__":
    print("=" * 70)
    print("     ANALISE SEMANTICA - Compilador Lua")
    print("     Atividade 6 - LFT")
    print("=" * 70)

    teste1_codigo_correto()
    teste2_codigo_com_erros()
    teste3_escopos()
    teste4_for_com_erro()
