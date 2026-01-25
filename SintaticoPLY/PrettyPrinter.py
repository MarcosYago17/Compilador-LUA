from SintaticoPLY.SintaxeAbstrata import ASTVisitor

class PrettyPrinter(ASTVisitor):
    def __init__(self):
        self.indent = 0
    
    def _i(self):
        return "    " * self.indent
    
    def visit_Block(self, node):
        return "\n".join(self.visit(stmt) for stmt in (node.statements or []))
    
    def visit_FunctionDecl(self, node):
        params = ", ".join(node.params)
        self.indent += 1
        body = self.visit(node.body)
        self.indent -= 1
        return f"function {node.name}({params})\n{body}\n{self._i()}end"
    
    def visit_Assign(self, node):
        return f"{self._i()}local {node.name} = {self.visit(node.exp)}"
    
    def visit_If(self, node):
        result = f"{self._i()}if {self.visit(node.condition)} then\n"
        self.indent += 1
        result += self.visit(node.then_body)
        self.indent -= 1
        for cond, block in node.elseifs:
            result += f"\n{self._i()}elseif {self.visit(cond)} then\n"
            self.indent += 1
            result += self.visit(block)
            self.indent -= 1
        if node.else_body:
            result += f"\n{self._i()}else\n"
            self.indent += 1
            result += self.visit(node.else_body)
            self.indent -= 1
        return result + f"\n{self._i()}end"
    
    def visit_While(self, node):
        self.indent += 1
        body = self.visit(node.body)
        self.indent -= 1
        return f"{self._i()}while {self.visit(node.condition)} do\n{body}\n{self._i()}end"
    
    def visit_ForNum(self, node):
        step = f", {self.visit(node.step)}" if node.step else ""
        self.indent += 1
        body = self.visit(node.body)
        self.indent -= 1
        return f"{self._i()}for {node.var} = {self.visit(node.start)}, {self.visit(node.end)}{step} do\n{body}\n{self._i()}end"
    
    def visit_ForGen(self, node):
        names = ", ".join(node.names)
        exps = ", ".join(self.visit(e) for e in node.exps)
        self.indent += 1
        body = self.visit(node.body)
        self.indent -= 1
        return f"{self._i()}for {names} in {exps} do\n{body}\n{self._i()}end"
    
    def visit_RepeatUntil(self, node):
        self.indent += 1
        body = self.visit(node.body)
        self.indent -= 1
        return f"{self._i()}repeat\n{body}\n{self._i()}until {self.visit(node.condition)}"
    
    def visit_Return(self, node):
        return f"{self._i()}return {self.visit(node.exp)}"
    
    def visit_Break(self, node):
        return f"{self._i()}break"
    
    def visit_FunctionCall(self, node):
        args = ", ".join(self.visit(a) for a in node.args)
        return f"{self._i()}{node.name}({args})"
    
    def visit_BinOp(self, node):
        return f"({self.visit(node.left)} {node.op} {self.visit(node.right)})"
    
    def visit_UnOp(self, node):
        return f"({node.op} {self.visit(node.operand)})"
    
    def visit_Concat(self, node):
        return f"({self.visit(node.left)} .. {self.visit(node.right)})"
    
    def visit_Length(self, node):
        return f"#{self.visit(node.operand)}"
    
    def visit_Number(self, node):
        return str(node.value)
    
    def visit_String(self, node):
        return f'"{node.value}"'
    
    def visit_Var(self, node):
        return node.name
    
    def visit_Boolean(self, node):
        return "true" if node.value else "false"
    
    def visit_Nil(self, node):
        return "nil"
