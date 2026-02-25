import os
import sys

import ply.yacc as yacc

# Adiciona o diretório raiz ao path para imports absolutos.
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if raiz not in sys.path:
    sys.path.insert(0, raiz)

try:
    from . import SintaxeAbstrata as a
    from . import AbstractVisitor
except ImportError:
    import SintaxeAbstrata as a
    import AbstractVisitor

from ExpressionLanguageParser import *  # noqa: F401,F403


class VisitorPrettyPrinter(AbstractVisitor.AbstractVisitor):
    def __init__(self):
        super().__init__()
        self.indent_level = 0

    def _indent(self):
        return "    " * self.indent_level

    def _node_name(self, node):
        return node.value if hasattr(node, "value") else str(node)

    def _iter_elseif(self, elseif_list):
        for item in elseif_list or []:
            if isinstance(item, tuple) and len(item) == 2:
                yield item
            elif hasattr(item, "condition") and hasattr(item, "then_body"):
                yield item.condition, item.then_body

    # --- Expressoes ---
    def visitNumber(self, node):
        return str(node.value)

    def visitString(self, node):
        return f'"{node.value}"'

    def visitVar(self, node):
        return str(node.name)

    def visitBoolean(self, node):
        return "true" if node.value else "false"

    def visitNil(self, node):
        return "nil"

    def visitUnOp(self, node):
        op = node.op.strip() if isinstance(node.op, str) else str(node.op)
        operand = node.operand.accept(self)
        if op == "not":
            return f"not {operand}"
        return f"{op}{operand}"

    def visitBinOp(self, node):
        return f"({node.left.accept(self)} {node.op} {node.right.accept(self)})"

    def visitFunctionCall(self, node):
        args = ", ".join(arg.accept(self) for arg in node.args)
        name = self._node_name(node.name)
        return f"{name}({args})"

    # --- Statements ---
    def visitBlock(self, node):
        if not node.statements:
            return ""
        lines = []
        for stmt in node.statements:
            text = stmt.accept(self)
            if not text:
                continue
            if stmt.__class__.__name__ == "FunctionCall":
                text = f"{self._indent()}{text}"
            lines.append(text)
        return "\n".join(lines)

    def visitAssign(self, node):
        name = self._node_name(node.name)
        prefix = "local " if getattr(node, "is_local", False) else ""
        return f"{self._indent()}{prefix}{name} = {node.exp.accept(self)}"

    def visitFunctionDecl(self, node):
        name = self._node_name(node.name)
        params = ", ".join(self._node_name(p) for p in node.params)
        lines = [f"{self._indent()}function {name}({params})"]
        self.indent_level += 1
        body = node.body.accept(self)
        if body:
            lines.append(body)
        self.indent_level -= 1
        lines.append(f"{self._indent()}end")
        return "\n".join(lines)

    def visitFor(self, node):
        var = self._node_name(node.var)
        start = node.start.accept(self)
        end = node.end.accept(self)
        step = node.step.accept(self) if node.step else "1"
        lines = [f"{self._indent()}for {var} = {start}, {end}, {step} do"]
        self.indent_level += 1
        body = node.body.accept(self)
        if body:
            lines.append(body)
        self.indent_level -= 1
        lines.append(f"{self._indent()}end")
        return "\n".join(lines)

    def visitWhile(self, node):
        condition = node.condition.accept(self)
        lines = [f"{self._indent()}while {condition} do"]
        self.indent_level += 1
        body = node.body.accept(self)
        if body:
            lines.append(body)
        self.indent_level -= 1
        lines.append(f"{self._indent()}end")
        return "\n".join(lines)

    def visitReturn(self, node):
        if node.exp is None:
            return f"{self._indent()}return"
        return f"{self._indent()}return {node.exp.accept(self)}"

    def visitIf(self, node):
        lines = [f"{self._indent()}if {node.condition.accept(self)} then"]

        self.indent_level += 1
        then_text = node.then_body.accept(self)
        if then_text:
            lines.append(then_text)
        self.indent_level -= 1

        for elseif_cond, elseif_body in self._iter_elseif(node.elseif_list):
            lines.append(f"{self._indent()}elseif {elseif_cond.accept(self)} then")
            self.indent_level += 1
            elseif_text = elseif_body.accept(self)
            if elseif_text:
                lines.append(elseif_text)
            self.indent_level -= 1

        if node.else_body:
            lines.append(f"{self._indent()}else")
            self.indent_level += 1
            else_text = node.else_body.accept(self)
            if else_text:
                lines.append(else_text)
            self.indent_level -= 1

        lines.append(f"{self._indent()}end")
        return "\n".join(lines)


def main():
    codigo_lua = """
    function soma(a, b)
        return a + b
    end

    local x = 10.5
    local y = 20

    while x < y do
        print(x)
        x = x + 1
    end

    if x == y then
        print("Iguais")
    else
        print("Diferentes")
    end
    """

    print("--- Testando Parser ---")
    parser = yacc.yacc()
    result = parser.parse(codigo_lua)

    if result:
        print("\n[OK] Parsing bem-sucedido")
        print(f"Numero de statements: {len(result.statements)}\n")
        print("--- Executando PrettyPrinter ---\n")
        vp = VisitorPrettyPrinter()
        codigo_regenerado = result.accept(vp)
        print("=" * 70)
        print("CODIGO LUA REGENERADO:")
        print("=" * 70)
        print(codigo_regenerado)
        print("=" * 70)
    else:
        print("[ERRO] Erro no parsing")


if __name__ == "__main__":
    main()
