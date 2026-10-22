import csv
pend = 0
ver = 0
with open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv') as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] != 'F01':
            continue
        if row['estado'] == 'pendiente':
            pend += 1
        elif row['estado'] == 'verificado' and row['verificado_por'].startswith('autor+F01'):
            ver += 1
print(f'pendiente F01: {pend}')
print(f'verificado F01.*: {ver}')
print(f'total: {pend + ver}')