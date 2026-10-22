import json
from pathlib import Path
total = 0
ids = []
units_dir = Path('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units')
for p in sorted(units_dir.glob('[!_]*.json')):
    u = json.load(open(p))
    if u['id'].startswith('B'):
        continue
    if u['id'] in ('F01.0', 'F01.6.0'):
        continue
    n = u.get('archivos_total', 0)
    ids.append((u['id'], n))
    total += n
print(f'Total: {total}')
for i, n in ids:
    print(f'  {n:5} {i}')