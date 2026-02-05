# Rascunho da Gramática
# 
# program     → statements
# statements  → statement statements | statement | ε (vazio)
#
# statement   → local ID = exp                  (Declaração Local)
#             | ID = exp                        (Atribuição)
#             | function ID ( params ) block end (Função)
#             | if exp then block end           (If Simples)
#             | if exp then block else block end(If/Else)
#             | return exp                      (Retorno)
#             | call                            (Chamada solta)
#
# block       → statements
#
# params      → ID , params | ID | ε
#
# call        → ID ( args )
# args        → exp , args | exp | ε
#
# exp         → exp + exp | exp - exp | exp * exp | exp / exp
#             | exp == exp | exp < exp | exp > exp
#             | call | number | string | ID

import ply.yacc as yacc
from LexicoPLY.ExpressionLanguageLex import tokens
from SintaticoPLY import SintaxeAbstrata as sa
# Precedência
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'EQUALS', 'LT', 'GT', 'LTEQUALS', 'GTEQUALS'),
    ('left', 'PLUS', 'MINUS'),    
    ('left', 'TIMES', 'DIVIDE'),
    ('right', 'UMINUS','NOT'),
)

# definição de trecho
def p_program(p):
    '''program : statements
               | empty '''
    p[0] = sa.Block(p[1])

# lista de comandos
def p_statements_multiple(p):
    '''statements : statement statements'''
    p[0] = [p[1]] + p[2]

def p_statements_single(p):
    '''statements : statement'''
    p[0] = [p[1]]

# Declaração de Função: função nomeFunção(parametro1, parametro2) ... end
def p_statement_funcdecl(p):
    '''statement : FUNCTION NAME LPAREN parameters RPAREN statements END'''
    p[0] = sa.FunctionDecl(p[2], p[4], sa.Block(p[6]))

def p_statement_for(p):
    '''statement : FOR NAME ATRIB expression COMMA expression DO statements END
                 | FOR NAME ATRIB expression COMMA expression COMMA expression DO statements END'''
    
    var_name = p[2]     
    start_exp = p[4]
    
    # Caso 1: SEM passo (len = 10) -> for i = 1, 10 do ...
    if len(p) == 10:
        end_exp = p[6]
        step_exp = None # ou sa.Number(1) se preferir
        body = sa.Block(p[8])
        
    # Caso 2: COM passo (len = 12) -> for i = 1, 10, 2 do ...
    else:
        end_exp = p[6]
        step_exp = p[8]
        body = sa.Block(p[10])

    p[0] = sa.For(var_name, start_exp, end_exp, step_exp, body)


# If / Else
def p_statement_if(p):
    '''statement : IF expression THEN statements END'''
    p[0] = sa.If(p[2], sa.Block(p[4]), None, None)

def p_statement_if_else(p):
    '''statement : IF expression THEN statements ELSE statements END'''
    p[0] = sa.If(p[2], sa.Block(p[4]), sa.Block(p[6]), None)
    
def p_statement_if_elseif_else(p):
    '''statement : IF expression THEN statements elseif_list ELSE statements END'''
    p[0] = sa.If(p[2], sa.Block(p[4]), sa.Block(p[7]), p[5])

def p_statement_if_elseif(p):
    '''statement : IF expression THEN statements elseif_list END'''
    p[0] = sa.If(p[2], sa.Block(p[4]), None, p[5])

def p_elseif_list(p):
    '''elseif_list : elseif_list ELSEIF expression THEN statements
                   | empty'''  
    if len(p) == 6:
        block_node = sa.Block(p[5])
        p[0] = p[1] + [(p[3], block_node)]
    else:
        p[0] = []

#-----------------------
def p_empty(p):
    'empty :'
    pass

#-----------------------

# Atribuição: local x = 10
def p_statement_assign_local(p):
    '''statement : LOCAL NAME ATRIB expression'''
    p[0] = sa.Assign(p[2], p[4])

# Atribuição existente: x = 10
def p_statement_assign(p):
    '''statement : NAME ATRIB expression'''
    p[0] = sa.Assign(p[1], p[3])

# Print é um caso especial de chamada de função em lua
def p_statement_print(p):
    '''statement : PRINT LPAREN expression RPAREN'''
    p[0] = sa.FunctionCall("print", [p[3]])

# Retorno
def p_statement_return(p):
    '''statement : RETURN expression'''
    p[0] = sa.Return(p[2])

# Chamada de função solta: funcao(x)
def p_statement_call(p):
    '''statement : function_call'''
    p[0] = p[1]

# parametros e argumentos 

# Parâmetros na declaração: (a, b, c)
def p_parameters_multi(p):
    '''parameters : NAME COMMA parameters'''
    p[0] = [p[1]] + p[3]

def p_parameters_single(p):
    '''parameters : NAME'''
    p[0] = [p[1]]

def p_parameters_empty(p):
    '''parameters : '''
    p[0] = []

# Argumentos na chamada: (10, x, x+1)
def p_arguments_multi(p):
    '''arguments : expression COMMA arguments'''
    p[0] = [p[1]] + p[3]

def p_arguments_single(p):
    '''arguments : expression'''
    p[0] = [p[1]]

def p_arguments_empty(p):
    '''arguments : '''
    p[0] = []

# EXPRESSÕES

def p_expression_uminus(p):
    '''expression : MINUS expression %prec UMINUS'''
    p[0] = sa.BinOp(sa.Number(0), '-', p[2]) 

def p_expression_not(p):
    '''expression : NOT expression'''
    p[0] = sa.UnOp('not', p[2])

def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression
                  | expression TIMES expression
                  | expression DIVIDE expression
                  | expression EQUALS expression
                  | expression LTEQUALS expression
                  | expression GTEQUALS expression
                  | expression LT expression
                  | expression GT expression
                  | expression AND expression
                  | expression OR expression'''
    p[0] = sa.BinOp(p[1], p[2], p[3])

def p_expression_call(p):
    '''expression : function_call'''
    p[0] = p[1]

# Regra auxiliar para chamada de função (usada tanto em expression quanto statement)
def p_function_call(p):
    '''function_call : NAME LPAREN arguments RPAREN'''
    p[0] = sa.FunctionCall(p[1], p[3])

def p_expression_atom(p):
    '''expression : NUMBER
                  | STRING
                  | NAME
                  | TRUE
                  | FALSE
                  | NIL'''
    if isinstance(p[1], int):
        p[0] = sa.Number(p[1])
    elif isinstance(p[1], str) and p[1].startswith('"'): # Verificação simplista
        p[0] = sa.String(p[1])
    elif p.slice[1].type == 'NAME': 
        p[0] = sa.Var(p[1])
    elif p.slice[1].type == 'TRUE':
        p[0] = sa.Boolean(True) 
    elif p.slice[1].type == 'FALSE':
        p[0] = sa.Boolean(False)
    elif p.slice[1].type == 'NIL':
        p[0] = sa.Nil() 

def p_error(p):
    if p:
        print(f"ERRO DE SINTAXE: Token '{p.value}' inesperado na linha {p.lineno}")
    else:
        print("ERRO DE SINTAXE: Final de arquivo inesperado")


 # --- TESTE ---

def main():
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
    print(result)

if __name__ == "__main__":
    main()