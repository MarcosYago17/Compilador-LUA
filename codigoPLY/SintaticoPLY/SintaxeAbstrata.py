# -------------------------
# SintaxeAbstrata.py (Versão Completa)
# -------------------------

class AST:
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

class Boolean(AST):
    def __init__(self, value):
        self.value = value  
    def __repr__(self): 
        return f"Bool({self.value})"

class Nil(AST):
    def __init__(self):
        pass 
    def __repr__(self): 
        return "Nil"

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


class For(AST):
    def __init__(self, var, start, end, step, body):
        self.var = var      
        self.start = start  
        self.end = end      
        self.step = step    
        self.body = body    
        
    def __repr__(self):
        return f"For({self.var} = {self.start} to {self.end} step {self.step}) {self.body}"

class Return(AST): 
    def __init__(self, exp):
        self.exp = exp
    def __repr__(self): return f"Return({self.exp})"

class If(AST):
    def __init__(self, condition, then_body, else_body=None, elseif_list=None):
        self.condition = condition
        self.then_body = then_body
        self.else_body = else_body
        self.elseif_list = elseif_list if elseif_list else []
    def __repr__(self): return f"If({self.condition}) Then {self.then_body} ElseIf {self.elseif_list} Else {self.else_body}"

class Block(AST): 
    def __init__(self, statements):
        self.statements = statements
    def __repr__(self): return f"Block{self.statements}"