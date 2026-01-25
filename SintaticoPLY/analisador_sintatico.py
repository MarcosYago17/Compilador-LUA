import sys
import os
import ply.yacc as yacc

# Ajuste de caminho para importar o Lexer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from LexicoPLY.ExpressionLanguageLEx import tokens, lexer

# --- PRECEDÊNCIA DE OPERADORES ---
precedence = (
    ('left', 'OR'),
    ('left', 'AND'),
    ('left', 'LT', 'GT', 'LTEQUALS', 'GTEQUALS', 'EQUALS', 'DIF'),
    ('right', 'CONCAT'),
    ('left', 'PLUS', 'MINUS'),
    ('left', 'TIMES', 'DIVIDE', 'PERCENTUAL'),
    ('right', 'NOT', 'TAG', 'UMINUS'),
    ('right', 'EXPO'),
)

# --- REGRAS GRAMATICAIS ---

# 1. ROOT (CHUNK)
def p_chunk(p):
    '''chunk : block'''
    p[0] = ('program', p[1])

# 2. BLOCOS
def p_block(p):
    '''block : statlist'''
    p[0] = p[1] if p[1] else []

def p_statlist_empty(p):
    '''statlist : '''
    p[0] = []

def p_statlist_stat(p):
    '''statlist : statlist stat'''
    p[0] = p[1] + [p[2]]

def p_statlist_semi(p):
    '''statlist : statlist SEMICOLON'''
    p[0] = p[1]

# 3. STATEMENTS

# Atribuição simples: NAME = exp
def p_stat_simple_assign(p):
    '''stat : NAME ATRIB explist'''
    p[0] = ('assign', [('var', p[1])], p[3])

# Atribuição com índice: NAME[exp] = exp ou NAME.field = exp
def p_stat_index_assign(p):
    '''stat : NAME COLCH exp RCOLCH ATRIB explist'''
    p[0] = ('assign', [('index', ('var', p[1]), p[3])], p[6])

def p_stat_field_assign(p):
    '''stat : NAME DOT NAME ATRIB explist'''
    p[0] = ('assign', [('field', ('var', p[1]), p[3])], p[5])

# Chamada de função como statement
def p_stat_call(p):
    '''stat : NAME LPAREN RPAREN
            | NAME LPAREN explist RPAREN'''
    if len(p) == 4:
        p[0] = ('call_stat', ('call', ('var', p[1]), []))
    else:
        p[0] = ('call_stat', ('call', ('var', p[1]), p[3]))

# Chamada com método: obj:metodo()
def p_stat_method_call(p):
    '''stat : NAME COLON NAME LPAREN RPAREN
            | NAME COLON NAME LPAREN explist RPAREN'''
    if len(p) == 6:
        p[0] = ('call_stat', ('method_call', ('var', p[1]), p[3], []))
    else:
        p[0] = ('call_stat', ('method_call', ('var', p[1]), p[3], p[5]))

# LOCAL
def p_stat_local(p):
    '''stat : LOCAL namelist ATRIB explist
            | LOCAL namelist'''
    if len(p) == 5:
        p[0] = ('local_assign', p[2], p[4])
    else:
        p[0] = ('local_decl', p[2])

# LOCAL FUNCTION
def p_stat_local_function(p):
    '''stat : LOCAL FUNCTION NAME LPAREN parlist RPAREN block END'''
    p[0] = ('local_function', p[3], p[5], p[7])

# --- ESTRUTURAS DE CONTROLE ---

def p_stat_if(p):
    '''stat : IF exp THEN block elseif_list else_part END'''
    p[0] = ('if', p[2], p[4], p[5], p[6])

def p_elseif_list_empty(p):
    '''elseif_list : '''
    p[0] = []

def p_elseif_list(p):
    '''elseif_list : elseif_list ELSEIF exp THEN block'''
    p[0] = p[1] + [('elseif', p[3], p[5])]

def p_else_part_empty(p):
    '''else_part : '''
    p[0] = None

def p_else_part(p):
    '''else_part : ELSE block'''
    p[0] = p[2]

def p_stat_while(p):
    '''stat : WHILE exp DO block END'''
    p[0] = ('while', p[2], p[4])

def p_stat_repeat(p):
    '''stat : REPEAT block UNTIL exp'''
    p[0] = ('repeat', p[2], p[4])

# For numérico
def p_stat_for_num(p):
    '''stat : FOR NAME ATRIB exp COMMA exp DO block END
            | FOR NAME ATRIB exp COMMA exp COMMA exp DO block END'''
    if len(p) == 10:
        p[0] = ('for_num', p[2], p[4], p[6], ('number', 1), p[8])
    else:
        p[0] = ('for_num', p[2], p[4], p[6], p[8], p[10])

# For genérico
def p_stat_for_in(p):
    '''stat : FOR namelist IN explist DO block END'''
    p[0] = ('for_in', p[2], p[4], p[6])

# Break e Return
def p_stat_break(p):
    '''stat : BREAK'''
    p[0] = ('break',)

def p_stat_return(p):
    '''stat : RETURN
            | RETURN explist'''
    if len(p) == 2:
        p[0] = ('return', None)
    else:
        p[0] = ('return', p[2])

# FUNCTION
def p_stat_function(p):
    '''stat : FUNCTION funcname LPAREN parlist RPAREN block END'''
    p[0] = ('function_def', p[2], p[4], p[6])

# DO block END
def p_stat_do(p):
    '''stat : DO block END'''
    p[0] = ('do', p[2])

# --- LISTAS AUXILIARES ---

def p_namelist_single(p):
    '''namelist : NAME'''
    p[0] = [p[1]]

def p_namelist_multi(p):
    '''namelist : namelist COMMA NAME'''
    p[0] = p[1] + [p[3]]

def p_explist_single(p):
    '''explist : exp'''
    p[0] = [p[1]]

def p_explist_multi(p):
    '''explist : explist COMMA exp'''
    p[0] = p[1] + [p[3]]

def p_parlist_empty(p):
    '''parlist : '''
    p[0] = []

def p_parlist_names(p):
    '''parlist : namelist'''
    p[0] = p[1]

def p_parlist_varargs(p):
    '''parlist : VARARGS'''
    p[0] = ['...']

def p_parlist_names_varargs(p):
    '''parlist : namelist COMMA VARARGS'''
    p[0] = p[1] + ['...']

def p_funcname(p):
    '''funcname : NAME
                | funcname DOT NAME'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ('field', p[1], p[3])

def p_funcname_method(p):
    '''funcname : funcname COLON NAME'''
    p[0] = ('method', p[1], p[3])

# --- EXPRESSÕES ---

def p_exp_binop(p):
    '''exp : exp PLUS exp
           | exp MINUS exp
           | exp TIMES exp
           | exp DIVIDE exp
           | exp PERCENTUAL exp
           | exp EXPO exp
           | exp CONCAT exp
           | exp AND exp
           | exp OR exp
           | exp LT exp
           | exp GT exp
           | exp LTEQUALS exp
           | exp GTEQUALS exp
           | exp EQUALS exp
           | exp DIF exp'''
    p[0] = ('binop', p[2], p[1], p[3])

def p_exp_unary(p):
    '''exp : MINUS exp %prec UMINUS
           | NOT exp
           | TAG exp'''
    p[0] = ('unop', p[1], p[2])

def p_exp_group(p):
    '''exp : LPAREN exp RPAREN'''
    p[0] = p[2]

def p_exp_number(p):
    '''exp : NUMBER'''
    p[0] = ('number', p[1])

def p_exp_string(p):
    '''exp : STRING'''
    p[0] = ('string', p[1])

def p_exp_true(p):
    '''exp : TRUE'''
    p[0] = ('bool', True)

def p_exp_false(p):
    '''exp : FALSE'''
    p[0] = ('bool', False)

def p_exp_nil(p):
    '''exp : NIL'''
    p[0] = ('nil', None)

def p_exp_varargs(p):
    '''exp : VARARGS'''
    p[0] = ('varargs',)

# Variável simples
def p_exp_var(p):
    '''exp : NAME'''
    p[0] = ('var', p[1])

# Acesso a índice: t[k]
def p_exp_index(p):
    '''exp : NAME COLCH exp RCOLCH'''
    p[0] = ('index', ('var', p[1]), p[3])

# Acesso a campo: t.k
def p_exp_field(p):
    '''exp : NAME DOT NAME'''
    p[0] = ('field', ('var', p[1]), p[3])

# Chamada de função em expressão
def p_exp_call(p):
    '''exp : NAME LPAREN RPAREN
           | NAME LPAREN explist RPAREN'''
    if len(p) == 4:
        p[0] = ('call', ('var', p[1]), [])
    else:
        p[0] = ('call', ('var', p[1]), p[3])

# Chamada de método em expressão: obj:metodo()
def p_exp_method_call(p):
    '''exp : NAME COLON NAME LPAREN RPAREN
           | NAME COLON NAME LPAREN explist RPAREN'''
    if len(p) == 6:
        p[0] = ('method_call', ('var', p[1]), p[3], [])
    else:
        p[0] = ('method_call', ('var', p[1]), p[3], p[5])

# Função anônima
def p_exp_function(p):
    '''exp : FUNCTION LPAREN parlist RPAREN block END'''
    p[0] = ('function_anon', p[3], p[5])

# Construtor de tabela
def p_exp_table(p):
    '''exp : BRACE fieldlist RBRACE
           | BRACE RBRACE'''
    if len(p) == 4:
        p[0] = ('table', p[2])
    else:
        p[0] = ('table', [])

def p_fieldlist_single(p):
    '''fieldlist : field'''
    p[0] = [p[1]]

def p_fieldlist_multi(p):
    '''fieldlist : fieldlist fieldsep field'''
    p[0] = p[1] + [p[3]]

def p_fieldlist_trailing(p):
    '''fieldlist : fieldlist fieldsep'''
    p[0] = p[1]

def p_fieldsep(p):
    '''fieldsep : COMMA
               | SEMICOLON'''
    pass

def p_field_bracket(p):
    '''field : COLCH exp RCOLCH ATRIB exp'''
    p[0] = ('field_bracket', p[2], p[5])

def p_field_name(p):
    '''field : NAME ATRIB exp'''
    p[0] = ('field_name', p[1], p[3])

def p_field_exp(p):
    '''field : exp'''
    p[0] = ('field_exp', p[1])

# --- TRATAMENTO DE ERROS ---
def p_error(p):
    if p:
        print(f"Erro de sintaxe no token '{p.value}' (tipo: {p.type}, linha {p.lineno})")
    else:
        print("Erro de sintaxe no final do arquivo (EOF)")

# --- BUILD ---
parser = yacc.yacc()