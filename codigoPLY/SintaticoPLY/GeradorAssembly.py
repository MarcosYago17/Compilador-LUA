import sys
import os
from ply import yacc

try:
    from . import SintaxeAbstrata as a
    from . import AbstractVisitor
except ImportError:
    import SintaxeAbstrata as a
    import AbstractVisitor

class GeradorAssembly(AbstractVisitor.AbstractVisitor):
    def __init__(self):
        super().__init__()
        # Secções do Assembly MIPS
        self.data_section = [".data\n"]
        self.text_section = [".text\n.globl main\nmain:\n"]
        
        # Gestão de Registradores Temporários ($t0 a $t9)
        self.reg_count = 0
        
        # Gestão de Rótulos (Labels para Ifs e Loops)
        self.label_count = 0
        
        # Variáveis e Strings já declaradas na secção .data
        self.variaveis_declaradas = set()
        self.strings_declaradas = {}
        self.str_count = 0

    def _get_reg(self):
        """Retorna um registrador temporário livre."""
        reg = f"$t{self.reg_count}"
        self.reg_count = (self.reg_count + 1) % 10
        return reg

    def _get_label(self, prefix="L"):
        """Gera um rótulo único."""
        lbl = f"{prefix}{self.label_count}"
        self.label_count += 1
        return lbl

    def _emit(self, instruction):
        """Adiciona uma instrução na secção text."""
        self.text_section.append(f"    {instruction}\n")

    # ==========================================
    # EXPRESSÕES (Retornam o registrador usado)
    # ==========================================

    def visitNumber(self, node):
        reg = self._get_reg()
        self._emit(f"li {reg}, {node.value}  # Carrega numero")
        return reg

    def visitString(self, node):
        # MIPS precisa que strings fiquem no .data
        if node.value not in self.strings_declaradas:
            lbl = f"str_{self.str_count}"
            self.str_count += 1
            self.strings_declaradas[node.value] = lbl
            self.data_section.append(f'{lbl}: .asciiz "{node.value}\\n"\n')
        
        lbl = self.strings_declaradas[node.value]
        reg = self._get_reg()
        self._emit(f"la {reg}, {lbl}  # Carrega endereco da string")
        return reg

    def visitBoolean(self, node):
        reg = self._get_reg()
        val = 1 if node.value else 0
        self._emit(f"li {reg}, {val}  # Carrega boolean")
        return reg

    def visitNil(self, node):
        reg = self._get_reg()
        self._emit(f"li {reg}, 0  # Nil tratado como 0")
        return reg

    def visitVar(self, node):
        # node.name pode ser str ou objeto String
        nome_var = node.name.value if hasattr(node.name, 'value') else node.name
        reg = self._get_reg()
        
        if nome_var not in self.variaveis_declaradas:
            self.variaveis_declaradas.add(nome_var)
            self.data_section.append(f"{nome_var}: .word 0\n")
            
        self._emit(f"lw {reg}, {nome_var}  # Le variavel {nome_var}")
        return reg

    def visitUnOp(self, node):
        reg_op = node.operand.accept(self)
        reg_res = self._get_reg()
        
        if node.op == '-':
            self._emit(f"neg {reg_res}, {reg_op}")
        elif node.op.strip() == 'not':
            self._emit(f"seq {reg_res}, {reg_op}, $zero  # Inverte boolean")
            
        return reg_res

    def visitBinOp(self, node):
        reg_esq = node.left.accept(self)
        reg_dir = node.right.accept(self)
        reg_res = self._get_reg()

        op = node.op.strip()
        if op == '+':
            self._emit(f"add {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '-':
            self._emit(f"sub {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '*':
            self._emit(f"mul {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '/':
            self._emit(f"div {reg_res}, {reg_esq}, {reg_dir}")
        # Comparações
        elif op == '==':
            self._emit(f"seq {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '~=':
            self._emit(f"sne {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '>':
            self._emit(f"sgt {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '<':
            self._emit(f"slt {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '>=':
            self._emit(f"sge {reg_res}, {reg_esq}, {reg_dir}")
        elif op == '<=':
            self._emit(f"sle {reg_res}, {reg_esq}, {reg_dir}")
        elif op == 'and':
            self._emit(f"and {reg_res}, {reg_esq}, {reg_dir}")
        elif op == 'or':
            self._emit(f"or {reg_res}, {reg_esq}, {reg_dir}")

        return reg_res

    def visitFunctionCall(self, node):
        nome_func = node.name.value if hasattr(node.name, 'value') else node.name
        
        # Tratamento especial para o PRINT do Lua
        if nome_func == "print" and len(node.args) > 0:
            arg_node = node.args[0]
            reg_val = arg_node.accept(self)
            
            self._emit(f"move $a0, {reg_val}")
            
            # Se for string, syscall 4. Se for numero/bool, syscall 1
            if isinstance(arg_node, a.String):
                self._emit("li $v0, 4  # Syscall print_string")
            else:
                self._emit("li $v0, 1  # Syscall print_int")
                
            self._emit("syscall")
            
            # Imprime quebra de linha após o print numérico
            if not isinstance(arg_node, a.String):
                if "\\n" not in self.strings_declaradas:
                    self.strings_declaradas["\\n"] = "newline"
                    self.data_section.append('newline: .asciiz "\\n"\n')
                self._emit("la $a0, newline")
                self._emit("li $v0, 4")
                self._emit("syscall")
                
        return self._get_reg()

    # ==========================================
    # COMANDOS (Statements)
    # ==========================================

    def visitBlock(self, node):
        if node.statements:
            for stmt in node.statements:
                stmt.accept(self)

    def visitAssign(self, node):
        nome_var = node.name.value if hasattr(node.name, 'value') else node.name
        
        # Registra a variável na secção .data se for a primeira vez
        if nome_var not in self.variaveis_declaradas:
            self.variaveis_declaradas.add(nome_var)
            self.data_section.append(f"{nome_var}: .word 0\n")

        # Avalia a expressão
        reg_val = node.exp.accept(self)
        
        # Salva na memória
        self._emit(f"sw {reg_val}, {nome_var}  # Salva em {nome_var}")

    def visitIf(self, node):
        lbl_else = self._get_label("Else")
        lbl_fim = self._get_label("FimIf")

        # Avalia Condição
        reg_cond = node.condition.accept(self)
        
        # Se for 0 (False), pula pro Else ou pro Fim
        if node.else_body or node.elseif_list:
            self._emit(f"beq {reg_cond}, $zero, {lbl_else}")
        else:
            self._emit(f"beq {reg_cond}, $zero, {lbl_fim}")

        # Corpo do Then
        node.then_body.accept(self)
        self._emit(f"j {lbl_fim}")

        # Else / ElseIf (Simplificado apenas para o Else básico)
        if node.else_body or node.elseif_list:
            self.text_section.append(f"{lbl_else}:\n")
            if node.else_body:
                node.else_body.accept(self)
        
        self.text_section.append(f"{lbl_fim}:\n")

    def visitFor(self, node):
        nome_var = node.var.value if hasattr(node.var, 'value') else node.var
        lbl_inicio = self._get_label("ForInicio")
        lbl_fim = self._get_label("ForFim")

        # Garante que a variável do For existe
        if nome_var not in self.variaveis_declaradas:
            self.variaveis_declaradas.add(nome_var)
            self.data_section.append(f"{nome_var}: .word 0\n")

        # Inicializa o 'start'
        reg_start = node.start.accept(self)
        self._emit(f"sw {reg_start}, {nome_var}  # Inicia {nome_var}")

        # Marca o início do laço
        self.text_section.append(f"{lbl_inicio}:\n")

        # Condição de parada (compara com o 'end')
        reg_var = self._get_reg()
        self._emit(f"lw {reg_var}, {nome_var}")
        reg_end = node.end.accept(self)
        
        # Se var > end, sai do loop
        self._emit(f"bgt {reg_var}, {reg_end}, {lbl_fim}")

        # Corpo do For
        node.body.accept(self)

        # Incremento (Step)
        reg_passo = node.step.accept(self) if node.step else self.visitNumber(a.Number(1))
        self._emit(f"lw {reg_var}, {nome_var}")
        self._emit(f"add {reg_var}, {reg_var}, {reg_passo} # Incrementa for")
        self._emit(f"sw {reg_var}, {nome_var}")

        # Volta pro começo
        self._emit(f"j {lbl_inicio}")
        
        # Fim do laço
        self.text_section.append(f"{lbl_fim}:\n")

    # Funções omitidas na geração básica (Stubs)
    def visitFunctionDecl(self, node):
        self._emit("# [AVISO] Declaracao de Funcoes omitida no Assembly basico")
        pass

    def visitReturn(self, node):
        self._emit("# [AVISO] Retorno omitido no Assembly basico")
        pass

    def exportar(self, filename="programa.asm"):
        """Gera o arquivo final."""
        # Syscall 10 para encerrar programa corretamente
        self._emit("li $v0, 10")
        self._emit("syscall")

        codigo = "".join(self.data_section) + "\n" + "".join(self.text_section)
        
        with open(filename, "w") as f:
            f.write(codigo)
        print(f"Assembly gerado com sucesso: {filename}")
        return codigo
    
# --- Bloco de Teste ---
if __name__ == "__main__":
    import os
    
    # 1. Adicionamos a pasta pai ao sys.path para conseguir importar o Parser
    import sys
    raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if raiz not in sys.path:
        sys.path.insert(0, raiz)
        
    # 2. Importamos o parser pronto (do seu arquivo ExpressionLanguageParser)
    from ExpressionLanguageParser import *
    import ply.yacc as yacc

    codigo_lua = """
    local x = 10
    local y = 20

    if x < y then
        print("X e menor que Y")
    else
        print("X e maior ou igual")
    end

    for i = 1, 5, 1 do
        print(i)
    end
    """

    print("--- Construindo Parser ---")
    # Agora ele constrói o parser usando as regras do arquivo importado
    parser = yacc.yacc() 
    arvore = parser.parse(codigo_lua)

    if arvore:
        print("\n✓ Parsing bem-sucedido! Gerando Assembly...")
        gerador = GeradorAssembly()
        arvore.accept(gerador)
        
        # Pega a pasta exata onde o GeradorAssembly.py está salvo
        pasta_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_completo = os.path.join(pasta_atual, "meu_codigo.asm")
        
        gerador.exportar(caminho_completo)
        print(f"✅ Arquivo salvo com sucesso em: {caminho_completo}")
    else:
        print("✗ Erro no parsing. A árvore retornou None.")