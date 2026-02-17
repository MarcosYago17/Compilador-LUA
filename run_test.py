import sys, os
# Navigate to the correct directory
script_dir = os.path.dirname(os.path.abspath(__file__))
target = os.path.join(script_dir, 'codigoPLY', 'SintaticoPLY')
os.chdir(target)
sys.path.insert(0, target)
sys.path.insert(0, os.path.join(script_dir, 'codigoPLY'))

# Now run the semantic analyzer
exec(open(os.path.join(target, 'VisitorSemantico.py'), encoding='utf-8').read())
