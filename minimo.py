import os
here = os.path.dirname(os.path.abspath(__file__))
out = os.path.join(here, 'prova.txt')
with open(out, 'w') as f:
    f.write('Python funcionou! Path: ' + here)
