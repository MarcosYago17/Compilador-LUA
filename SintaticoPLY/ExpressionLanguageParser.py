# Rascunho da Gramática
# 
# program     → statements
# statements  → statement statements | statement | ε (vazio)
#
# statement   → local ID = exp                  (Declaração Local)
#             | ID = exp                        (Atribuição)
#             | function ID ( params ) block end (Função)
#             | while exp do block end          (Loop)
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
    ('left', 'EQUALS', 'LT', 'GT'),
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

# Loop While: while (x < 10) do ... end
def p_statement_while(p):
    '''statement : WHILE expression DO statements END'''
    p[0] = sa.While(p[2], sa.Block(p[4])) #remover

def p_statement_for_numeric(p):
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

    p[0] = sa.ForNum(var_name, start_exp, end_exp, step_exp, body)

def p_statement_for_generic(p):
    '''statement : FOR namelist IN explist DO statements END'''
    p[0] = sa.ForGen(p[2], p[4], sa.Block(p[6]))#remover

# AUXILIARES PARA O FOR GENÉRICO

def p_namelist(p):
    '''namelist : NAME COMMA namelist
                | NAME'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

def p_explist(p):
    '''explist : expression COMMA explist
               | expression'''
    if len(p) == 4:
        p[0] = [p[1]] + p[3]
    else:
        p[0] = [p[1]]

# If / Else
def p_statement_if(p):
    '''statement : IF expression THEN statements END'''
    p[0] = sa.If(p[2], sa.Block(p[4]))

def p_statement_if_else(p):
    '''statement : IF expression THEN statements ELSE statements END'''
    p[0] = sa.If(p[2], sa.Block(p[4]), sa.Block(p[6]))
    
def p_elseif_list(p):
    '''elseif_list : elseif_list ELSEIF expression THEN statements
                   | empty'''
    if len(p) == 6:
        p[0] = p[1] + [(p[3], p[5])]
    else:
        p[0] = []

def p_empty(p):
    'empty :'   #remover
    pass

# Atribuição: local x = 10
def p_statement_assign_local(p):
    '''statement : LOCAL NAME EQUALS expression'''
    p[0] = sa.Assign(p[2], p[4])

# Atribuição existente: x = 10
def p_statement_assign(p):
    '''statement : NAME EQUALS expression'''
    p[0] = sa.Assign(p[1], p[3])

# Print é um caso especial de chamada de função em lua
def p_statement_print(p):
    '''statement : PRINT LPAREN expression RPAREN'''
    # aqui vamos lidar como um comando
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
                  | expression LT expression
                  | expression GT expression'''
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
                  | NAME'''
    if isinstance(p[1], int):
        p[0] = sa.Number(p[1])
    elif isinstance(p[1], str) and p[1].startswith('"'): # Verificação simplista
        p[0] = sa.String(p[1])
    elif p.slice[1].type == 'NAME': # Verifica se o token é NAME
        p[0] = sa.Var(p[1])
    else:
        p[0] = sa.String(p[1])

def p_error(p):
    if p:
        print(f"ERRO DE SINTAXE: Token '{p.value}' inesperado na linha {p.lineno}")
    else:
        print("ERRO DE SINTAXE: Final de arquivo inesperado")


 # --- TESTE ---

def main():
    # Código Lua mais complexo para teste
    codigo_lua = """
    function soma(a, b)
        return a + b
    end

    local x = 10
    local y = 20
    
    while x < y do
        x = soma(x, 1)
        print(x)
    end
    """
    
    print("--- Testando Parser ---")
    parser = yacc.yacc()
    result = parser.parse(codigo_lua)
    print(result)

if __name__ == "__main__":
    main()