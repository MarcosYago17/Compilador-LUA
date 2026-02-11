import SintaxeAbstrata as a
import AbstractVisitor
import sys
import os
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(raiz)
#from LexicoPLY.ExpressionLanguageLex import tokens
from ExpressionLanguageParser import *

'''
todas as classes retornam String, pois fica mais fácil de testar
e muito mais visível para erros
'''
class VisitorPrettyPrinter(AbstractVisitor.AbstractVisitor):
    
    '''
    super init é para inicializar o mecanismo do visitor corretamente
    sem ele, os testes não conseguem alcançar os métodos abstratos
    '''
    def __init__(self):
        super().__init__()  # Garante inicialização da base
        self.indent_level = 0  # Se usado

    def _indent(self):
        return "    " * self.indent_level
    
    # --- Expressões ---
    def visitNumber(self, node):
        return str(node.value)

    def visitString(self, node):
        return f'"{node.value}"'

    def visitVar(self, node):
        # Na sua classe Var, o atributo é 'name'
        return str(node.name)

    def visitBoolean(self, node):
        return "true" if node.value else "false"

    def visitNil(self, node):
        return "nil"

    def visitUnOp(self, node):
        return f"{node.op}{node.operand.accept(self)}"

    
    def visitBinOp(self, node):
        return f"({node.left.accept(self)} {node.op} {node.right.accept(self)})"

    def visitFunctionCall(self, node):
        args = ", ".join([arg.accept(self) for arg in node.args])
        return f"{node.name}({args})"

    # --- Comandos (Statements) ---
    def visitBlock(self, node):
        lines = [f"{self._indent()}{stmt.accept(self)}" for stmt in node.statements]
        return "\n".join(lines)

    def visitAssign(self, node):
        # Na sua classe Assign, os atributos são 'name' e 'exp'
        # return f"{node.name.accept(self)} = {node.exp.accept(self)}"
        return f"{node.name} = {node.exp.accept(self)}"
    
    def visitFunctionDecl(self, node):
        # params = ", ".join([p.accept(self) for p in node.params])
        params = ", ".join([p for p in node.params])

        body = node.body.accept(self)
        return f"function {node.name}({params})\n{body}\n{self._indent()}end"

    def visitFor(self, node):
        # Em Lua: for var = start, end, step do
        var = node.var.accept(self)
        start = node.start.accept(self)
        end = node.end.accept(self)
        step = node.step.accept(self)
        body = node.body.accept(self)
        return f"for {var} = {start}, {end}, {step} do\n{body}\n{self._indent()}end"

    def visitReturn(self, node):
        # Na classe Return, o atributo é 'exp'
        val = node.exp.accept(self) if node.exp else ""
        return f"return {val}"

    def visitIf(self, node):
        # Na classe If, os atributos são 'condition', 'then_body', 'else_body'
        cond = node.condition.accept(self)
        then_part = node.then_body.accept(self)
        res = f"if {cond} then\n{then_part}"
        
        # Tratando a lista de ElseIf
        if node.elseif_list:
            for ei in node.elseif_list:
                # Caso ei tenha a mesma estrutura de um nó If
                res += f"\n{self._indent()}elseif {ei.condition.accept(self)} then"
                res += f"\n{ei.then_body.accept(self)}"
        
        if node.else_body:
            res += f"\n{self._indent()}else\n{node.else_body.accept(self)}"
            
        res += f"\n{self._indent()}end"
        return res


def main():
        # Teste 1: x = 1 + 2
    # Note que Assign agora recebe (name, exp)
    expr = a.BinOp(a.Number(1), "+", a.Number(2))
    atribuicao = a.Assign(a.Var("x"), expr)

    # Teste 2: If x > 10
    condicao = a.BinOp(a.Var("x"), ">", a.Number(10))
    corpo = a.Block([a.Assign(a.Var("y"), a.Number(100))])
    meu_if = a.If(condicao, corpo)

    visitor = VisitorPrettyPrinter()
    
    print("--- Atribuição ---")
    print(atribuicao.accept(visitor))
    
    print("\n--- Estrutura If ---")
    print(meu_if.accept(visitor))
    
    #expressões simples
    print("\n=== Expressões básicas ===")
    print(a.Number(10).accept(visitor))          # 10
    print(a.String("lua").accept(visitor))        # "lua"
    print(a.Boolean(True).accept(visitor))        # true
    print(a.Boolean(False).accept(visitor))       # false
    print(a.Nil().accept(visitor))                # nil
    print(a.Var("x").accept(visitor))             # x
    
    #UnOp
    print("\n=== UnOp ===")
    expr1 = a.UnOp("-", a.Number(5))
    expr2 = a.UnOp("not ", a.Boolean(False))

    print(expr1.accept(visitor))   # -5
    print(expr2.accept(visitor))   # not false
    
    #functionCall
    
    print("\n=== FunctionCall ===")
    call = a.FunctionCall(
        "print",
        [a.String("resultado"), a.BinOp(a.Number(2), "+", a.Number(3))]
    )

    print(call.accept(visitor))
    # print("resultado", (2 + 3))
    
    #Assign
    print("\n=== Assign ===")
    assign = a.Assign(
        a.Var("x"),
        a.BinOp(a.Number(10), "/", a.Number(2))
    )

    print(assign.accept(visitor))
    # x = (10 / 2)
    
    #block
    print("\n=== Block ===")
    block = a.Block([
        a.Assign(a.Var("a"), a.Number(1)),
        a.Assign(a.Var("b"), a.Number(2)),
        a.Assign(a.Var("c"), a.BinOp(a.Var("a"), "+",a.Var("b"))),
        call
    ])

    print(block.accept(visitor))
    
    #For
    print("\n=== For ===")
    loop = a.For(
        a.Var("i"),
        a.Number(1),
        a.Number(10),
        a.Number(1),
        a.Block([
            a.FunctionCall("print", [a.Var("i")])
        ])
    )

    print(loop.accept(visitor))
    
    #if/else/elseif
    
    print("\n=== If / ElseIf / Else ===")
    if_node = a.If(
        condition=a.BinOp(a.Var("x"), ">", a.Number(0)),
        then_body=a.Block([
            a.FunctionCall("print", [a.String("positivo")])
        ]),
        else_body=a.Block([
            a.FunctionCall("print", [a.String("negativo ou zero")])
        ]),
        elseif_list=[
            a.If(
                condition=a.BinOp(a.Var("x"), "==", a.Number(0)),
                then_body=a.Block([
                    a.FunctionCall("print", [a.String("zero")])
                ])
            )
        ]
    )

    print(if_node.accept(visitor))

def main2():
    
    codigo_lua = """
    function soma(a, b)
        return a + b
    end

    local x = 10

    local y = 20

    for i = 1, 10, 2 do
        print(i)
    end

    if x == y then
        print("Iguais")
    else
        print("Diferentes")
    end
    
    local nota = 8

    if nota > 7 then
        print("Aprovado")
    elseif nota > 5 then
        print("Recuperação")
    else
        print("Reprovado")
    end

    function somar(a, b)
        return a + b
    end

    local resultado = somar(10, 5)
    
    function coordenadas()
        return 10
    end

    local x = coordenadas()

    local saldo = 100
        print(divida)
    local divida = -saldo
        print(-divida)
    
    local vivo = true
    local morto = not vivo

    print(morto)
    print(not nil)
    print(not 0)

    local texto = "Lua"
        print(texto)

    if x > 0 and y < 10 then
        print("ok")
    end

    if a or b then
        print("verdadeiro")
    end
    """
    
    print("--- Testando Parser ---")
    parser = yacc.yacc()
    result = parser.parse(codigo_lua)
    #print(result.statements[0])  # Imprime a primeira declaração (a função soma)
    vp = VisitorPrettyPrinter()
    #print (type(result))
    result.accept(vp)

# --- Bloco de Teste Atualizado ---
if __name__ == "__main__":
    main2()