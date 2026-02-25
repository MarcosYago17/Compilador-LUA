import os
import sys

import ply.yacc as yacc

try:
    from . import SintaxeAbstrata as a
    from . import AbstractVisitor
except ImportError:
    import SintaxeAbstrata as a
    import AbstractVisitor


class GeradorAssembly(AbstractVisitor.AbstractVisitor):
    def __init__(self):
        super().__init__()

        self.data_section = [".data\n"]
        self.main_section = []
        self.function_section = []
        self._active_section = self.main_section

        self.reg_count = 0
        self.label_count = 0
        self.str_count = 0

        self.variaveis_declaradas = set()
        self.strings_declaradas = {}
        self.function_signatures = {}
        self.generated_functions = set()

        self.current_function = None
        self.current_function_end_label = None

    # ------------------------------------------
    # Helpers
    # ------------------------------------------

    def _emit(self, instruction):
        self._active_section.append(f"    {instruction}\n")

    def _emit_label(self, label):
        self._active_section.append(f"{label}:\n")

    def _get_reg(self):
        reg = f"$t{self.reg_count}"
        self.reg_count = (self.reg_count + 1) % 10
        return reg

    def _get_label(self, prefix="L"):
        label = f"{prefix}{self.label_count}"
        self.label_count += 1
        return label

    def _node_name(self, node):
        return node.value if hasattr(node, "value") else str(node)

    def _escape_string(self, value):
        return value.replace("\\", "\\\\").replace('"', '\\"')

    def _ensure_variable(self, name):
        if name not in self.variaveis_declaradas:
            self.variaveis_declaradas.add(name)
            self.data_section.append(f"{name}: .word 0\n")

    def _declare_string(self, value):
        if value not in self.strings_declaradas:
            label = f"str_{self.str_count}"
            self.str_count += 1
            self.strings_declaradas[value] = label
            escaped = self._escape_string(value)
            self.data_section.append(f'{label}: .asciiz "{escaped}"\n')
        return self.strings_declaradas[value]

    def _ensure_newline_label(self):
        if "\n" not in self.strings_declaradas:
            self.strings_declaradas["\n"] = "newline"
            self.data_section.append('newline: .asciiz "\\n"\n')
        return self.strings_declaradas["\n"]

    def _is_string_literal(self, node):
        return node.__class__.__name__ == "String"

    def _iter_elseif(self, elseif_list):
        for item in elseif_list or []:
            if isinstance(item, tuple) and len(item) == 2:
                yield item
            elif hasattr(item, "condition") and hasattr(item, "then_body"):
                yield item.condition, item.then_body

    def _register_function_signature(self, node):
        name = self._node_name(node.name)
        params = [self._node_name(p) for p in node.params]
        if name not in self.function_signatures:
            self.function_signatures[name] = {
                "label": f"func_{name}",
                "params": params,
            }
        return self.function_signatures[name]

    # ------------------------------------------
    # Expressoes
    # ------------------------------------------

    def visitNumber(self, node):
        reg = self._get_reg()
        self._emit(f"li {reg}, {node.value}")
        return reg

    def visitString(self, node):
        label = self._declare_string(node.value)
        reg = self._get_reg()
        self._emit(f"la {reg}, {label}")
        return reg

    def visitBoolean(self, node):
        reg = self._get_reg()
        self._emit(f"li {reg}, {1 if node.value else 0}")
        return reg

    def visitNil(self, node):
        reg = self._get_reg()
        self._emit(f"li {reg}, 0")
        return reg

    def visitVar(self, node):
        nome = self._node_name(node.name)
        self._ensure_variable(nome)
        reg = self._get_reg()
        self._emit(f"lw {reg}, {nome}")
        return reg

    def visitUnOp(self, node):
        reg_op = node.operand.accept(self)
        reg_res = self._get_reg()
        op = node.op.strip() if isinstance(node.op, str) else node.op

        if op == "-":
            self._emit(f"neg {reg_res}, {reg_op}")
        elif op == "not":
            self._emit(f"seq {reg_res}, {reg_op}, $zero")
        else:
            self._emit(f"move {reg_res}, {reg_op}")
        return reg_res

    def visitBinOp(self, node):
        reg_esq = node.left.accept(self)
        reg_dir = node.right.accept(self)
        reg_res = self._get_reg()
        op = node.op.strip() if isinstance(node.op, str) else node.op

        if op == "+":
            self._emit(f"add {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "-":
            self._emit(f"sub {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "*":
            self._emit(f"mul {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "/":
            self._emit(f"div {reg_esq}, {reg_dir}")
            self._emit(f"mflo {reg_res}")
        elif op == "==":
            self._emit(f"seq {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "~=":
            self._emit(f"sne {reg_res}, {reg_esq}, {reg_dir}")
        elif op == ">":
            self._emit(f"sgt {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "<":
            self._emit(f"slt {reg_res}, {reg_esq}, {reg_dir}")
        elif op == ">=":
            self._emit(f"sge {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "<=":
            self._emit(f"sle {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "and":
            self._emit(f"and {reg_res}, {reg_esq}, {reg_dir}")
        elif op == "or":
            self._emit(f"or {reg_res}, {reg_esq}, {reg_dir}")
        else:
            self._emit(f"li {reg_res}, 0  # operador nao suportado: {op}")

        return reg_res

    def visitFunctionCall(self, node):
        nome_func = self._node_name(node.name)

        if nome_func == "print":
            if node.args:
                arg_node = node.args[0]
                reg_val = arg_node.accept(self)
                self._emit(f"move $a0, {reg_val}")
                if self._is_string_literal(arg_node):
                    self._emit("li $v0, 4  # print_string")
                else:
                    self._emit("li $v0, 1  # print_int")
                self._emit("syscall")

                newline_label = self._ensure_newline_label()
                self._emit(f"la $a0, {newline_label}")
                self._emit("li $v0, 4")
                self._emit("syscall")
            reg_out = self._get_reg()
            self._emit(f"li {reg_out}, 0")
            return reg_out

        assinatura = self.function_signatures.get(nome_func)
        if not assinatura:
            self._emit(f"# [ERRO] Funcao '{nome_func}' nao declarada")
            reg_out = self._get_reg()
            self._emit(f"li {reg_out}, 0")
            return reg_out

        for idx, arg_node in enumerate(node.args):
            reg_arg = arg_node.accept(self)
            if idx < 4:
                self._emit(f"move $a{idx}, {reg_arg}")
            else:
                self._emit("# [AVISO] Mais de 4 argumentos nao suportados")

        self._emit(f"jal {assinatura['label']}")
        reg_out = self._get_reg()
        self._emit(f"move {reg_out}, $v0")
        return reg_out

    # ------------------------------------------
    # Statements
    # ------------------------------------------

    def visitBlock(self, node):
        statements = node.statements or []
        for stmt in statements:
            if stmt.__class__.__name__ == "FunctionDecl":
                self._register_function_signature(stmt)
        for stmt in statements:
            stmt.accept(self)

    def visitAssign(self, node):
        nome = self._node_name(node.name)
        self._ensure_variable(nome)
        reg_val = node.exp.accept(self)
        self._emit(f"sw {reg_val}, {nome}")

    def visitIf(self, node):
        end_label = self._get_label("IfEnd")
        next_label = self._get_label("IfNext")

        reg_cond = node.condition.accept(self)
        self._emit(f"beq {reg_cond}, $zero, {next_label}")
        node.then_body.accept(self)
        self._emit(f"j {end_label}")
        self._emit_label(next_label)

        for elseif_cond, elseif_body in self._iter_elseif(node.elseif_list):
            elseif_next = self._get_label("IfNext")
            reg_elseif = elseif_cond.accept(self)
            self._emit(f"beq {reg_elseif}, $zero, {elseif_next}")
            elseif_body.accept(self)
            self._emit(f"j {end_label}")
            self._emit_label(elseif_next)

        if node.else_body:
            node.else_body.accept(self)

        self._emit_label(end_label)

    def visitFor(self, node):
        nome_var = self._node_name(node.var)
        self._ensure_variable(nome_var)

        loop_start = self._get_label("ForStart")
        loop_end = self._get_label("ForEnd")

        reg_start = node.start.accept(self)
        self._emit(f"sw {reg_start}, {nome_var}")
        self._emit_label(loop_start)

        reg_var = self._get_reg()
        self._emit(f"lw {reg_var}, {nome_var}")
        reg_end = node.end.accept(self)
        self._emit(f"bgt {reg_var}, {reg_end}, {loop_end}")

        node.body.accept(self)

        reg_step = node.step.accept(self) if node.step else self.visitNumber(a.Number(1))
        self._emit(f"lw {reg_var}, {nome_var}")
        self._emit(f"add {reg_var}, {reg_var}, {reg_step}")
        self._emit(f"sw {reg_var}, {nome_var}")
        self._emit(f"j {loop_start}")
        self._emit_label(loop_end)

    def visitWhile(self, node):
        loop_start = self._get_label("WhileStart")
        loop_end = self._get_label("WhileEnd")

        self._emit_label(loop_start)
        reg_cond = node.condition.accept(self)
        self._emit(f"beq {reg_cond}, $zero, {loop_end}")
        node.body.accept(self)
        self._emit(f"j {loop_start}")
        self._emit_label(loop_end)

    def visitFunctionDecl(self, node):
        assinatura = self._register_function_signature(node)
        nome = self._node_name(node.name)
        if nome in self.generated_functions:
            return

        self.generated_functions.add(nome)
        old_section = self._active_section
        old_function = self.current_function
        old_end_label = self.current_function_end_label

        self._active_section = self.function_section
        self.current_function = nome
        self.current_function_end_label = self._get_label(f"{assinatura['label']}_end")

        self._emit_label(assinatura["label"])
        self._emit("addiu $sp, $sp, -4")
        self._emit("sw $ra, 0($sp)")

        for idx, param_name in enumerate(assinatura["params"]):
            self._ensure_variable(param_name)
            if idx < 4:
                self._emit(f"sw $a{idx}, {param_name}")
            else:
                self._emit("# [AVISO] Mais de 4 parametros nao suportados")

        node.body.accept(self)
        self._emit("li $v0, 0")
        self._emit(f"j {self.current_function_end_label}")

        self._emit_label(self.current_function_end_label)
        self._emit("lw $ra, 0($sp)")
        self._emit("addiu $sp, $sp, 4")
        self._emit("jr $ra")

        self._active_section = old_section
        self.current_function = old_function
        self.current_function_end_label = old_end_label

    def visitReturn(self, node):
        if self.current_function_end_label is None:
            self._emit("# [AVISO] return fora de funcao foi ignorado")
            return

        if node.exp is not None:
            reg_val = node.exp.accept(self)
            self._emit(f"move $v0, {reg_val}")
        else:
            self._emit("li $v0, 0")
        self._emit(f"j {self.current_function_end_label}")

    # ------------------------------------------
    # Saida
    # ------------------------------------------

    def exportar(self, filename="programa.asm"):
        text_header = ".text\n.globl main\nmain:\n"
        main_tail = "    li $v0, 10\n    syscall\n"

        codigo = (
            "".join(self.data_section)
            + "\n"
            + text_header
            + "".join(self.main_section)
            + main_tail
            + "".join(self.function_section)
        )

        with open(filename, "w", encoding="utf-8") as file:
            file.write(codigo)
        print(f"Assembly gerado com sucesso: {filename}")
        return codigo


if __name__ == "__main__":
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if raiz not in sys.path:
        sys.path.insert(0, raiz)

    from ExpressionLanguageParser import *  # noqa: F401,F403

    codigo_lua = """
    function soma(a, b)
        return a + b
    end

    local x = 10
    local y = soma(x, 32)

    while x < y do
        print(x)
        x = x + 1
    end
    """

    print("--- Construindo Parser ---")
    parser = yacc.yacc()
    arvore = parser.parse(codigo_lua)

    if arvore:
        print("\n[OK] Parsing bem-sucedido! Gerando Assembly...")
        gerador = GeradorAssembly()
        arvore.accept(gerador)
        pasta_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_completo = os.path.join(pasta_atual, "meu_codigo.asm")
        gerador.exportar(caminho_completo)
        print(f"[OK] Arquivo salvo com sucesso em: {caminho_completo}")
    else:
        print("[ERRO] Erro no parsing. A arvore retornou None.")
