import ply.lex as lex

reserved = {
    'and': 'AND',
    'break': 'BREAK',
    'do': 'DO',
    'else': 'ELSE',
    'elseif': 'ELSEIF',
    'end': 'END',
    'false': 'FALSE',
    'for': 'FOR',
    'function': 'FUNCTION',
    'if': 'IF',
    'in': 'IN',
    'local': 'LOCAL',
    'nil': 'NIL',
    'not': 'NOT',
    'or': 'OR',
    'repeat': 'REPEAT',
    'return': 'RETURN',
    'then': 'THEN',
    'true': 'TRUE',
    'until': 'UNTIL',
    'while': 'WHILE',
}

tokens = [
    'NAME', 'NUMBER', 'STRING',
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'PERCENTUAL', 'EXPO', 'TAG',
    'EQUALS', 'DIF', 'LTEQUALS', 'GTEQUALS', 'LT', 'GT', 'ATRIB',
    'LPAREN', 'RPAREN', 'COLCH', 'RCOLCH', 'BRACE', 'RBRACE',
    'SEMICOLON', 'COLON', 'DUALCOLON', 'COMMA', 'DOT', 'CONCAT', 'VARARGS'
] + list(reserved.values())

t_ignore = ' \t'

t_PLUS = r'\+'
t_MINUS = r'-'
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_PERCENTUAL = r'%'
t_EXPO = r'\^'
t_TAG = r'\#'

t_EQUALS = r'=='
t_DIF = r'~='
t_LTEQUALS = r'<='
t_GTEQUALS = r'>='
t_LT = r'<'
t_GT = r'>'
t_ATRIB = r'='

t_LPAREN = r'\('
t_RPAREN = r'\)'
t_COLCH = r'\['
t_RCOLCH = r'\]'
t_BRACE = r'\{'
t_RBRACE = r'\}'

t_SEMICOLON = r';'
t_DUALCOLON = r'::'
t_COLON = r':'
t_COMMA = r','

def t_VARARGS(t):
    r'\.\.\.'
    return t

def t_CONCAT(t):
    r'\.\.'
    return t

def t_DOT(t):
    r'\.'
    return t

def t_NAME(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'NAME')
    return t

def t_NUMBER(t):
    r'(0[xX][0-9a-fA-F]+)|(\d+(\.\d+)?([eE][+-]?\d+)?)'
    if 'x' in t.value or 'X' in t.value:
        t.value = int(t.value, 16)
    else:
        t.value = float(t.value)
    return t

def t_STRING(t):
    r'("[^"\\]*(?:\\.[^"\\]*)*")|(\'[^\'\\]*(?:\\.[^\'\\]*)*\')'
    t.value = t.value[1:-1]
    return t

def t_COMMENT(t):
    r'--\[\[.*?\]\]|--.*'
    pass

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Erro léxico: caractere inválido '{t.value[0]}' na linha {t.lexer.lineno}")
    t.lexer.skip(1)

lexer = lex.lex()