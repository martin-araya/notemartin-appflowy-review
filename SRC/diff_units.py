"""Find F01 files in cobertura that are NOT in any F01 unidad."""
import csv
import json
from pathlib import Path

cov = '/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv'
units_dir = Path('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units')

# Collect all F01 files in unidades (excluding indices)
unit_files = set()
for p in sorted(units_dir.glob('[!_]*.json')):
    u = json.load(open(p))
    if u['id'].startswith('B'):
        continue
    if u['id'] in ('F01.0', 'F01.6.0'):
        continue
    for f in u.get('archivos', []):
        if isinstance(f, dict):
            k = (f['fuente'], f['ruta'])
            unit_files.add(k)

# Collect F01 rows from cobertura
cov_f01 = []
with open(cov) as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] != 'F01':
            continue
        cov_f01.append((row['fuente'], row['ruta']))

# Find cobertura entries not in unidades
unmatched = []
for k in cov_f01:
    if k not in unit_files:
        unmatched.append(k)
print(f'unmatched: {len(unmatched)}')
for u in unmatched[:30]:
    print(' ', u)