import csv
import re
from pathlib import Path

# Count F02 by source/folder
appflowy_db = 0
rust_db = 0
collab_db = 0
appflowy_cell = 0
appflowy_widget = 0
appflowy_filter = 0
appflowy_application = 0
appflowy_other = 0
total = 0
with open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv') as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] != 'F02':
            continue
        total += 1
        ruta = row['ruta']
        if 'rust-lib/flowy-database2' in ruta:
            rust_db += 1
        elif 'collab-database' in ruta:
            collab_db += 1
        elif 'plugins/database/application/cell' in ruta:
            appflowy_cell += 1
        elif 'plugins/database/widgets' in ruta:
            appflowy_widget += 1
        elif 'plugins/database/filter' in ruta or 'plugins/database/group' in ruta or 'plugins/database/sort' in ruta:
            appflowy_filter += 1
        elif 'plugins/database/application' in ruta:
            appflowy_application += 1
        else:
            appflowy_other += 1
print(f'Total F02: {total}')
print(f'  rust-lib/flowy-database2: {rust_db}')
print(f'  collab-database: {collab_db}')
print(f'  appflowy database/application/cell: {appflowy_cell}')
print(f'  appflowy database/widgets: {appflowy_widget}')
print(f'  appflowy database/filter|group|sort: {appflowy_filter}')
print(f'  appflowy database/application: {appflowy_application}')
print(f'  appflowy other database: {appflowy_other}')