"""
==========================================================
VisitorSemantico.py - Análise Semântica do Compilador Lua
Atividade 6 - Linguagens Formais e Tradutores (LFT)
==========================================================

O que este arquivo faz:
  Percorre a Árvore Sintática (AST) gerada pelo parser e
  verifica se o código faz SENTIDO. Exemplos de coisas que
  ele detecta:
    - Usar uma variável que nunca foi criada
    - Chamar uma função que não existe
    - Tentar somar texto com número
    - Erros nos valores do laço 'for'
"""

import sys
import os
import ply.yacc as yacc

# Ajuste de caminho para encontrar os outros arquivos
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, raiz)

# Importa os módulos do projeto (funciona tanto como módulo quanto executado direto)
try:
    from . import SintaxeAbstrata as a
    from . import AbstractVisitor
    from . import SymbolTable as st
except ImportError:
    import SintaxeAbstrata as a
    import AbstractVisitor
    import SymbolTable as st

# Importa o parser (regras gramaticais e tokens)
from ExpressionLanguageParser import *


class VisitorSemantico(AbstractVisitor.AbstractVisitor):
    """
    Visitor que percorre a AST e realiza análise semântica.

    O que ele verifica:
      1. Se variáveis foram declaradas antes de serem usadas
      2. Se funções foram declaradas antes de serem chamadas
      3. Se operações aritméticas usam tipos compatíveis
      4. Se o 'for' numérico usa valores numéricos
      5. Controle de escopos (funções, for, if criam escopos)
    """

    def __init__(self):
        super().__init__()
        self.erros = []       # Lista de erros encontrados
        self.avisos = []      # Lista de avisos (não impedem compilação)
        st.reset_table()      # Limpa a tabela de símbolos
        self._registrar_builtins()

    def _registrar_builtins(self):
        """
        Registra funções que já vêm prontas no Lua.
        Assim o analisador não reclama quando o código usa print(), type(), etc.
        """
        for nome in ['print', 'type', 'tostring', 'tonumber',
                      'pairs', 'ipairs', 'pcall', 'error',
                      'assert', 'require', 'unpack', 'select',
                      'rawget', 'rawset', 'setmetatable', 'getmetatable']:
            try:
                st.add_function(nome, params=None, return_type=None)
            except Exception:
                pass

    # ---------- Funções auxiliares ----------

    def _erro(self, mensagem):
        """Registra um erro semântico."""
        self.erros.append(f"[ERRO] {mensagem}")

    def _aviso(self, mensagem):
        """Registra um aviso."""
        self.avisos.append(f"[AVISO] {mensagem}")

    def _extrair_nome(self, node):
        """Pega o nome de um nó (pode ser objeto String ou texto puro)."""
        if hasattr(node, 'value'):
            return node.value
        return str(node)

    # ==============================================
    #          VISITANDO EXPRESSÕES
    # ==============================================

    def visitNumber(self, node):
        """Número: tipo 'number'."""
        return st.NUMBER

    def visitString(self, node):
        """Texto: tipo 'string'."""
        return st.STRING

    def visitBoolean(self, node):
        """Booleano: tipo 'boolean'."""
        return st.BOOLEAN

    def visitNil(self, node):
        """Nil: tipo 'nil'."""
        return st.NIL

    def visitVar(self, node):
        """
        Variável sendo USADA no código.
        Verifica: ela foi declarada antes?
        """
        if not st.symbol_exists(node.name):
            self._erro(
                f"Variável '{node.name}' usada sem ter sido declarada"
            )
            return None

        simbolo = st.lookup_symbol(node.name)
        return simbolo[st.TYPE] if simbolo else None

    def visitUnOp(self, node):
        """
        Operação com um valor só (ex: -x, not x).
        - Se for '-': verifica se o valor é número
        - Se for 'not': sempre retorna boolean
        """
        tipo = node.operand.accept(self)

        op = node.op.strip() if isinstance(node.op, str) else node.op

        if op == '-':
            if tipo and tipo != st.NUMBER:
                self._aviso(
                    f"Operador '-' aplicado a tipo '{tipo}' "
                    f"(esperado: number)"
                )
            return st.NUMBER
        elif op == 'not':
            return st.BOOLEAN

        return None

    def visitBinOp(self, node):
        """
        Operação com dois valores (ex: a + b, x == y).
        - Aritméticas (+, -, *, /): ambos devem ser number
        - Comparações (==, <, >, etc.): retorna boolean
        - Lógicas (and, or): retorna tipo do operando
        """
        tipo_esq = node.left.accept(self)
        tipo_dir = node.right.accept(self)

        if node.op in ['+', '-', '*', '/']:
            if tipo_esq and tipo_esq not in [st.NUMBER, st.NIL]:
                self._aviso(
                    f"Operador '{node.op}': lado esquerdo é "
                    f"'{tipo_esq}', esperado 'number'"
                )
            if tipo_dir and tipo_dir not in [st.NUMBER, st.NIL]:
                self._aviso(
                    f"Operador '{node.op}': lado direito é "
                    f"'{tipo_dir}', esperado 'number'"
                )
            return st.NUMBER

        elif node.op in ['==', '~=', '<', '>', '<=', '>=']:
            return st.BOOLEAN

        elif node.op in ['and', 'or']:
            return tipo_esq

        return None

    def visitFunctionCall(self, node):
        """
        Chamada de função (ex: soma(1, 2), print("oi")).
        Verifica:
          1. A função foi declarada?
          2. É realmente uma função?
          3. Número de argumentos bate?
        """
        nome = self._extrair_nome(node.name)

        if not st.symbol_exists(nome):
            self._erro(f"Função '{nome}' chamada sem ter sido declarada")
        else:
            simbolo = st.lookup_symbol(nome)

            if simbolo and simbolo[st.CATEGORY] != st.FUNC:
                self._aviso(
                    f"'{nome}' não é uma função, mas foi chamada como uma"
                )

            if simbolo and simbolo.get(st.PARAMS):
                esperados = len(simbolo[st.PARAMS])
                recebidos = len(node.args)
                if recebidos != esperados:
                    self._aviso(
                        f"Função '{nome}' espera {esperados} "
                        f"argumento(s), recebeu {recebidos}"
                    )

        # Visita cada argumento (pode ter erros dentro deles)
        for arg in node.args:
            arg.accept(self)

        return None

    # ==============================================
    #          VISITANDO COMANDOS
    # ==============================================

    def visitAssign(self, node):
        """
        Atribuição (ex: x = 10 ou local x = 10).
        1. Avalia a expressão do lado direito
        2. Registra ou atualiza a variável na tabela
        """
        nome = self._extrair_nome(node.name)

        # Primeiro avalia a expressão (pode ter erros nela)
        tipo_exp = node.exp.accept(self)

        # Se a variável já existe, atualiza o tipo
        if st.symbol_exists(nome):
            simbolo = st.lookup_symbol(nome)
            if simbolo:
                simbolo[st.TYPE] = tipo_exp
        else:
            # Variável nova: registra na tabela
            try:
                st.add_variable(
                    nome, var_type=tipo_exp, is_local=True
                )
            except Exception as e:
                self._erro(str(e))

    def visitFunctionDecl(self, node):
        """
        Declaração de função (ex: function soma(a, b) ... end).
        1. Registra a função
        2. Abre um novo escopo
        3. Registra parâmetros como variáveis locais
        4. Visita o corpo
        5. Fecha o escopo
        """
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
        """
        Laço for numérico (ex: for i = 1, 10, 2 do ... end).
        1. Abre escopo
        2. Registra variável do laço
        3. Verifica se início, fim e passo são números
        4. Visita o corpo
        5. Fecha escopo
        """
        st.enter_scope()

        nome_var = self._extrair_nome(node.var)
        try:
            st.add_variable(nome_var, var_type=st.NUMBER, is_local=True)
        except Exception as e:
            self._erro(str(e))

        tipo_ini = node.start.accept(self)
        if tipo_ini and tipo_ini != st.NUMBER:
            self._erro(
                f"For: valor inicial deve ser número, "
                f"recebeu '{tipo_ini}'"
            )

        tipo_fim = node.end.accept(self)
        if tipo_fim and tipo_fim != st.NUMBER:
            self._erro(
                f"For: valor final deve ser número, "
                f"recebeu '{tipo_fim}'"
            )

        if node.step:
            tipo_passo = node.step.accept(self)
            if tipo_passo and tipo_passo != st.NUMBER:
                self._erro(
                    f"For: passo deve ser número, "
                    f"recebeu '{tipo_passo}'"
                )

        node.body.accept(self)
        st.exit_scope()

    def visitReturn(self, node):
        """Visita a expressão do return."""
        if node.exp:
            return node.exp.accept(self)
        return st.NIL

    def visitIf(self, node):
        """
        Estrutura if/elseif/else.
        Cada bloco (then, elseif, else) tem seu próprio escopo.
        """
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
        """Visita cada comando dentro de um bloco."""
        if node.statements:
            for stmt in node.statements:
                stmt.accept(self)

    # ==============================================
    #              RELATÓRIO FINAL
    # ==============================================

    def relatorio(self):
        """Imprime o relatório completo da análise semântica."""
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
        print("RESULTADO:",
              "APROVADO (sem erros)" if sucesso
              else "REPROVADO (erros encontrados)")
        print("=" * 70 + "\n")
        return sucesso


# ==============================================
#                   TESTES
# ==============================================

def teste1_codigo_correto():
    """Código Lua SEM erros — tudo deve passar."""

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

    print("\n" + "#" * 70)
    print("  TESTE 1: Código CORRETO (nenhum erro esperado)")
    print("#" * 70)

    parser = yacc.yacc()
    arvore = parser.parse(codigo)

    if arvore:
        visitor = VisitorSemantico()
        arvore.accept(visitor)
        visitor.relatorio()
    else:
        print("Erro no parsing!")


def teste2_codigo_com_erros():
    """Código Lua COM erros — o analisador deve detectar."""

    codigo = """
    local x = 10

    local resultado = calcular(x)

    local texto = "lua"
    local conta = texto + 5

    print(y)
    """

    print("\n" + "#" * 70)
    print("  TESTE 2: Código COM ERROS (erros devem ser detectados)")
    print("  Erros esperados:")
    print("    - 'calcular' não foi declarada")
    print("    - 'texto + 5' mistura string com número")
    print("    - 'y' não foi declarada")
    print("#" * 70)

    parser = yacc.yacc()
    arvore = parser.parse(codigo)

    if arvore:
        visitor = VisitorSemantico()
        arvore.accept(visitor)
        visitor.relatorio()
    else:
        print("Erro no parsing!")


def teste3_escopos():
    """Teste focado em verificar escopos."""

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

    print("\n" + "#" * 70)
    print("  TESTE 3: Verificação de ESCOPOS")
    print("#" * 70)

    parser = yacc.yacc()
    arvore = parser.parse(codigo)

    if arvore:
        visitor = VisitorSemantico()
        arvore.accept(visitor)
        visitor.relatorio()
    else:
        print("Erro no parsing!")


def teste4_for_com_erro():
    """For com valor de string (deveria ser número)."""

    codigo = """
    for i = 1, 10, 2 do
        print(i)
    end
    """

    print("\n" + "#" * 70)
    print("  TESTE 4: Laço FOR numérico (deve passar)")
    print("#" * 70)

    parser = yacc.yacc()
    arvore = parser.parse(codigo)

    if arvore:
        visitor = VisitorSemantico()
        arvore.accept(visitor)
        visitor.relatorio()
    else:
        print("Erro no parsing!")


if __name__ == "__main__":
    print("=" * 70)
    print("     ANÁLISE SEMÂNTICA - Compilador Lua")
    print("     Atividade 6 - LFT")
    print("=" * 70)

    teste1_codigo_correto()
    teste2_codigo_com_erros()
    teste3_escopos()
    teste4_for_com_erro()
