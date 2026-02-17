import os
import subprocess
import sys

# Define o caminho do projeto
project_root = r'C:\Users\Yago\OneDrive\Documentos\Faculdade\6ª período Yago\LFT\Compilador-LUA\Compilador-LUA'
file_to_add = os.path.join('codigoPLY', 'SintaticoPLY', 'VisitorSemantico.py')

def run_git(args):
    try:
        # Usa shell=True e cwd para tentar contornar problemas de encoding no Windows
        result = subprocess.run(['git'] + args, cwd=project_root, capture_output=True, text=True, shell=True)
        print(f"> git {' '.join(args)}")
        if result.stdout: print(result.stdout)
        if result.stderr: print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"Erro ao rodar git: {e}")
        return False

print("--- Iniciando Operações de Git ---")
if run_git(['add', file_to_add]):
    if run_git(['commit', '-m', 'Atividade 6: Adicionando VisitorSemantico para análise semântica']):
        print("\nCommit realizado com sucesso!")
        # O push pode pedir senha se não estiver configurado SSH/Token
        # Mas vou tentar rodar
        if run_git(['push']):
            print("\nPush realizado com sucesso! Verifique seu GitHub.")
        else:
            print("\nErro no Push. Pode ser necessário configurar sua senha no VS Code.")
else:
    print("\nErro ao adicionar arquivo ao Git.")
