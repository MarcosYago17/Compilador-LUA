# -------------------------
# SintaxeAbstrata.py (Versão Completa)
# -------------------------

class AST:
    """Classe base para todos os nós da AST."""
    def accept(self, visitor):
        """Método para padrão Visitor."""
        method_name = f'visit_{type(self).__name__}'
        visit_method = getattr(visitor, method_name, visitor.generic_visit)
        return visit_method(self)
    
    def __repr__(self):
        return str(self.__dict__)

# expressões
class Number(AST):
    def __init__(self, value):
        self.value = value
    def __repr__(self): return f"Num({self.value})"

class String(AST):
    def __init__(self, value):
        self.value = value
    def __repr__(self): return f"Str('{self.value}')"

class Var(AST): 
    def __init__(self, name):
        self.name = name
    def __repr__(self): return f"Var({self.name})"

class UnOp(AST):
    def __init__(self, op, operand):
        self.op = op          # not ou '-'
        self.operand = operand # a expressão sendo negada
    def __repr__(self):
        return f"UnOp('{self.op}', {self.operand})"

class BinOp(AST): 
    def __init__(self, left, op, right):
        self.left = left
        self.op = op
        self.right = right
    def __repr__(self): return f"Op({self.left} {self.op} {self.right})"

class FunctionCall(AST): 
    def __init__(self, name, args):
        self.name = name
        self.args = args 
    def __repr__(self): return f"Call({self.name}, args={self.args})"

# comandos (statements)
class Assign(AST):
    def __init__(self, name, exp):
        self.name = name
        self.exp = exp
    def __repr__(self): return f"Assign({self.name} = {self.exp})"

class FunctionDecl(AST): 
    def __init__(self, name, params, body):
        self.name = name
        self.params = params 
        self.body = body     
    def __repr__(self): return f"Func {self.name}({self.params}) {self.body}"

class While(AST): 
    def __init__(self, condition, body):
        self.condition = condition
        self.body = body
    def __repr__(self): return f"While({self.condition}) {self.body}"

class ForNum(AST):
    def __init__(self, var, start, end, step, body):
        self.var = var      # Nome da variável (string)
        self.start = start  # Expressão inicial
        self.end = end      # Expressão final
        self.step = step    # Expressão do passo (pode ser None ou Num)
        self.body = body    # Bloco de comandos
        
    def __repr__(self):
        return f"ForNum({self.var} = {self.start} to {self.end} step {self.step}) {self.body}"

class ForGen(AST):
    def __init__(self, names, exps, body):
        self.names = names  # Lista de nomes das variáveis
        self.exps = exps    # Lista de expressões (ex: pairs(t))
        self.body = body    # Bloco de comandos
        
    def __repr__(self):
        return f"ForGen({self.names} in {self.exps}) {self.body}"

class Return(AST): 
    def __init__(self, exp):
        self.exp = exp
    def __repr__(self): return f"Return({self.exp})"

class If(AST):
    def __init__(self, condition, then_body, elseifs=None, else_body=None):
        self.condition = condition
        self.then_body = then_body
        self.elseifs = elseifs or []  # Lista de (condição, bloco)
        self.else_body = else_body
        
    def __repr__(self): 
        elseif_str = f" ElseIfs{self.elseifs}" if self.elseifs else ""
        return f"If({self.condition}) Then {self.then_body}{elseif_str} Else {self.else_body}"

class Block(AST): 
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self): return f"Block{self.statements}"

class Break(AST):
    """Representa o comando 'break' para sair de loops."""
    def __repr__(self): return "Break()"

class RepeatUntil(AST):
    """Representa o loop 'repeat ... until condition'."""
    def __init__(self, body, condition):
        self.body = body          # Bloco de statements
        self.condition = condition # Condição de parada
    def __repr__(self): 
        return f"RepeatUntil({self.body} until {self.condition})"

class Boolean(AST):
    """Representa os literais booleanos 'true' e 'false'."""
    def __init__(self, value):
        self.value = value  # True ou False
    def __repr__(self): return f"Bool({self.value})"

class Nil(AST):
    """Representa o literal 'nil'."""
    def __repr__(self): return "Nil()"

class Concat(AST):
    """Representa a operação de concatenação '..'."""
    def __init__(self, left, right):
        self.left = left
        self.right = right
    def __repr__(self): return f"Concat({self.left} .. {self.right})"

class Length(AST):
    """Representa o operador de tamanho '#'."""
    def __init__(self, operand):
        self.operand = operand
    def __repr__(self): return f"Len(#{self.operand})"


# -------------------------
# Visitor Base Class
# -------------------------

class ASTVisitor:
    """Classe base para visitantes da AST."""
    
    def visit(self, node):
        """Visita um nó da AST."""
        return node.accept(self)
    
    def generic_visit(self, node):
        """Método chamado quando não há visitante específico."""
        raise NotImplementedError(f"Visitor não implementado para {type(node).__name__}")
