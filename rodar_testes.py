import sys
import os

# Configurar paths
script_dir = os.path.dirname(os.path.abspath(__file__))
sintatico_dir = os.path.join(script_dir, 'codigoPLY', 'SintaticoPLY')
codigo_dir = os.path.join(script_dir, 'codigoPLY')

os.chdir(sintatico_dir)
sys.path.insert(0, sintatico_dir)
sys.path.insert(0, codigo_dir)

# Importa PLY e força uso de tabelas existentes (mais rápido)
import ply.yacc as yacc
import ply.lex as lex

# Monkey-patch para pular regeneração debug log
import logging
logging.getLogger('PLY').setLevel(logging.ERROR)

# Agora importa os módulos do projeto
import SintaxeAbstrata as a
import AbstractVisitor
import SymbolTable as st
from ExpressionLanguageParser import *

# Cria o parser com debug desabilitado e escrita de tabelas desativada
_parser = yacc.yacc(debug=False, write_tables=False, errorlog=logging.getLogger('PLY'))

# Redefine yacc.yacc nos testes para retornar o parser já criado
def _mock_yacc(*args, **kwargs):
    return _parser

yacc.yacc = _mock_yacc

# Agora importa o VisitorSemantico (que internamente usa yacc.yacc())
from VisitorSemantico import VisitorSemantico, teste1_codigo_correto, teste2_codigo_com_erros, teste3_escopos, teste4_for_com_erro

print("=" * 70)
print("     ANÁLISE SEMÂNTICA - Compilador Lua")
print("     Atividade 6 - LFT")
print("=" * 70)

teste1_codigo_correto()
teste2_codigo_com_erros()
teste3_escopos()
teste4_for_com_erro()
