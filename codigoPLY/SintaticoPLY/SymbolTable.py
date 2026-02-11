NUMBER = 'number'
STRING = 'string'
BOOLEAN = 'boolean'
NIL = 'nil'
TABLE = 'table'
FUNCTION = 'function'

# Categorias de símbolos
VARIABLE = 'var'
FUNC = 'fun'

# Campos do dicionário de símbolos
NAME = 'name'
TYPE = 'type'
CATEGORY = 'category'
PARAMS = 'params'
SCOPE = 'scope'
IS_LOCAL = 'is_local'
OFFSET = 'offset'
VALUE = 'value'


DEBUG = 0

# ===== VARIÁVEIS GLOBAIS =====
symbolTable = []  
scopeStack = [0]  
currentScope = 0  
curOffset = 0     


# ===== FUNÇÕES AUXILIARES =====

def reset_table():
    """Reseta a tabela de símbolos para o estado inicial."""
    global symbolTable, scopeStack, currentScope, curOffset
    symbolTable = []
    scopeStack = [0]
    currentScope = 0
    curOffset = 0


def enter_scope():
    """Entra em um novo escopo."""
    global currentScope, scopeStack
    currentScope += 1
    scopeStack.append(currentScope)
    if DEBUG > 0:
        print(f"[DEBUG] Entrando no escopo {currentScope}")
    return currentScope


def exit_scope():
    """Sai do escopo atual."""
    global scopeStack
    if len(scopeStack) <= 1:
        raise Exception("Erro: não é possível sair do escopo global")
    scopeStack.pop()
    if DEBUG > 0:
        print(f"[DEBUG] Saindo do escopo, voltando para {scopeStack[-1]}")


def get_current_scope():
    """Retorna o escopo atual."""
    return scopeStack[-1]


def add_symbol(name, category, symbol_type=None, params=None, is_local=False, value=None):
    """
    Adiciona um símbolo à tabela.
    
    Args:
        name: Nome do símbolo
        category: VARIABLE ou FUNC
        symbol_type: Tipo do símbolo (NUMBER, STRING, etc.)
        params: Lista de parâmetros (para funções)
        is_local: Se é uma variável local
        value: Valor inicial (opcional)
    """
    global symbolTable, curOffset
    
    # Verifica se o símbolo já existe no escopo atual
    scope = get_current_scope()
    for sym in symbolTable:
        if sym[NAME] == name and sym[SCOPE] == scope:
            raise Exception(f"Erro: símbolo '{name}' já declarado no escopo {scope}")
    
    # Cria o dicionário do símbolo
    symbol = {
        NAME: name,
        CATEGORY: category,
        TYPE: symbol_type,
        SCOPE: scope,
        IS_LOCAL: is_local,
        OFFSET: curOffset,
        VALUE: value
    }
    
    if category == FUNC:
        symbol[PARAMS] = params if params else []
    
    symbolTable.append(symbol)
    curOffset += 1
    
    if DEBUG > 0:
        print(f"[DEBUG] Símbolo adicionado: {symbol}")
        print_table()


def lookup_symbol(name, current_scope_only=False):
    """
    Procura um símbolo na tabela.
    
    Args:
        name: Nome do símbolo a procurar
        current_scope_only: Se True, procura apenas no escopo atual
    
    Returns:
        Dicionário do símbolo ou None se não encontrado
    """
    if current_scope_only:
        # Procura apenas no escopo atual
        scope = get_current_scope()
        for sym in reversed(symbolTable):
            if sym[NAME] == name and sym[SCOPE] == scope:
                return sym
    else:
        # Procura no escopo atual e nos escopos pais (escopo léxico)
        for sym in reversed(symbolTable):
            if sym[NAME] == name and sym[SCOPE] in scopeStack:
                return sym
    
    return None


def symbol_exists(name, current_scope_only=False):
    """Verifica se um símbolo existe na tabela."""
    return lookup_symbol(name, current_scope_only) is not None


def add_variable(name, var_type=None, is_local=False, value=None):
    """Adiciona uma variável à tabela de símbolos."""
    add_symbol(name, VARIABLE, symbol_type=var_type, is_local=is_local, value=value)


def add_function(name, params=None, return_type=None):
    """Adiciona uma função à tabela de símbolos."""
    add_symbol(name, FUNC, symbol_type=return_type, params=params)


def get_symbol_type(name):
    """Retorna o tipo de um símbolo."""
    sym = lookup_symbol(name)
    return sym[TYPE] if sym else None


def get_symbol_category(name):
    """Retorna a categoria de um símbolo (VARIABLE ou FUNC)."""
    sym = lookup_symbol(name)
    return sym[CATEGORY] if sym else None


def print_table():
    """Imprime o conteúdo da tabela de símbolos de forma legível."""
    print("\n" + "="*70)
    print("TABELA DE SÍMBOLOS")
    print("="*70)
    if not symbolTable:
        print("  (vazia)")
    else:
        for i, sym in enumerate(symbolTable):
            print(f"[{i}] {sym[NAME]:15} | Cat: {sym[CATEGORY]:8} | "
                  f"Type: {str(sym[TYPE]):10} | Scope: {sym[SCOPE]} | "
                  f"Local: {sym[IS_LOCAL]} | Offset: {sym[OFFSET]}")
            if sym[CATEGORY] == FUNC and sym.get(PARAMS):
                print(f"     Params: {sym[PARAMS]}")
    print("="*70)
    print(f"Escopo atual: {get_current_scope()}")
    print(f"Pilha de escopos: {scopeStack}")
    print("="*70 + "\n")



# ===== TESTES =====
def main():
    print("\n=== Testando SymbolTable (Abordagem Procedural) ===\n")
    
    # Resetar tabela
    reset_table()
    
    # Teste 1: Declarando variáveis globais
    print("1. Declarando variáveis no escopo global:")
    add_variable("x", var_type=NUMBER, is_local=False)
    add_variable("y", var_type=NUMBER, is_local=False)
    print_table()
    
    # Teste 2: Entrando em escopo de função
    print("\n2. Entrando em escopo de função 'soma':")
    enter_scope()
    add_function("soma", params=["a", "b"], return_type=NUMBER)
    add_variable("a", var_type=NUMBER, is_local=True)
    add_variable("b", var_type=NUMBER, is_local=True)
    print_table()
    
    # Teste 3: Procurando variáveis
    print("\n3. Procurando variáveis:")
    print(f"  'a' no escopo atual: {lookup_symbol('a', current_scope_only=True)}")
    print(f"  'x' no escopo atual: {lookup_symbol('x', current_scope_only=True)}")
    print(f"  'x' em qualquer escopo: {lookup_symbol('x', current_scope_only=False)}")
    
    # Teste 4: Entrando em bloco interno (if, for, etc.)
    print("\n4. Entrando em bloco interno:")
    enter_scope()
    add_variable("z", var_type=STRING, is_local=True)
    print_table()
    
    # Teste 5: Saindo dos escopos
    print("\n5. Saindo do bloco interno:")
    exit_scope()
    print_table()
    
    print("\n6. Saindo da função:")
    exit_scope()
    print_table()
    
    # Teste 7: Testando erro de redeclaração
    print("\n7. Testando erro de redeclaração:")
    try:
        add_variable("x", var_type=NUMBER, is_local=False)
    except Exception as e:
        print(f"  ✓ Erro capturado: {e}")
    
    # Teste 8: Testando lookup de símbolo não existente
    print("\n8. Procurando símbolo não existente:")
    result = lookup_symbol("nao_existe")
    print(f"  'nao_existe': {result}")
    
    # Teste 9: Verificando existência de símbolos
    print("\n9. Verificando existência de símbolos:")
    print(f"  'x' existe? {symbol_exists('x')}")
    print(f"  'soma' existe? {symbol_exists('soma')}")
    print(f"  'inexistente' existe? {symbol_exists('inexistente')}")
    
    # Teste 10: Obtendo informações de símbolos
    print("\n10. Obtendo informações de símbolos:")
    print(f"  Tipo de 'x': {get_symbol_type('x')}")
    print(f"  Categoria de 'soma': {get_symbol_category('soma')}")
    
    print("\n=== Fim dos Testes ===\n")


if __name__ == "__main__":
    main()
