import subprocess
import sys
import os

projeto = os.path.dirname(os.path.abspath(__file__))
sintatico = os.path.join(projeto, 'codigoPLY', 'SintaticoPLY')
output_file = os.path.join(projeto, 'resultado_testes.txt')

cmd = [
    sys.executable, '-u',
    os.path.join(sintatico, 'VisitorSemantico.py')
]

print(f"Rodando: {' '.join(cmd)}")
print(f"Diretório: {sintatico}")
print("Aguardando (timeout: 120s)...")

try:
    result = subprocess.run(
        cmd,
        cwd=sintatico,
        capture_output=True,
        text=True,
        timeout=120,
        encoding='utf-8',
        errors='replace'
    )
    output = result.stdout + result.stderr
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(output)
    print("CONCLUÍDO! Resultado salvo em resultado_testes.txt")
    print("=" * 60)
    print(output)
except subprocess.TimeoutExpired:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("TIMEOUT: processo excedeu 120 segundos\n")
    print("TIMEOUT: processo demorou mais de 120 segundos")
except Exception as e:
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"ERRO: {e}\n")
    print(f"ERRO: {e}")
