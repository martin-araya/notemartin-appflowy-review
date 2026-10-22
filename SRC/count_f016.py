import csv, json
from pathlib import Path

cov = '/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv'
unit_files = []
with open(cov) as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] == 'F01' and '/editor_plugins/' in row['ruta']:
            unit_files.append({'fuente': row['fuente'], 'ruta': row['ruta'], 'capa': row['capa'], 'estado': row['estado']})
print(f'Total: {len(unit_files)}')
unique = set(f['ruta'] for f in unit_files)
print(f'Unique: {len(unique)}')
PYEOF