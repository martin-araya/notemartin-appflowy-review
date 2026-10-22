import csv
from collections import Counter
c = Counter()
files = []
with open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv') as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] != 'F01':
            continue
        files.append((row['fuente'], row['ruta']))
        # Group by feature_id prefix + format
print(f'F01 unique files: {len(set(files))}')
print(f'F01 total rows: {len(files)}')
# Check F01 vs F01.x
f01_just = sum(1 for f in files if not f[1].startswith(('appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins',
                                                         'collab:',
                                                         )))
print(f'F01 non-editor_plugins: {f01_just}')