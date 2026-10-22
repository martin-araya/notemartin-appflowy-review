import json
import csv
from pathlib import Path

files = []
with open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv') as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] == 'F02' and 'database/' in row['ruta'] and ('editor_plugins' in row['ruta'] or 'rust-lib/flowy-database2' in row['ruta']):
            files.append({'fuente': row['fuente'], 'ruta': row['ruta'], 'capa': row['capa'], 'estado': row['estado']})

print(f'Total F02 + database paths: {len(files)}')

unit = {
    'schema_version': 1, 'id': 'F02.0.1', 'feature_id': 'F02', 'sub_index': 1,
    'titulo': 'Indice: DatabaseController, manager, modelo collab-database, layouts, template — appflowy',
    'fuentes': ['appflowy'], 'archivos': files, 'archivos_total': len(files),
    'catalogos': ['blocs.json','deps.json','events.json','misc.json','notifications.json','protobuf.json'],
    'catalogos_razon': {'events.json':'Eventos FFI / dispatch','blocs.json':'BLoCs / Cubits','protobuf.json':'Entidades protobuf','notifications.json':'Notificaciones','deps.json':'Dependencias','misc.json':'Rutas, atajos, flags, error codes, i18n'},
    'dependencias': [{'id':'F02.0','tipo':'indice','nota':'Documento indice F02.0 debe existir antes de esta sub-unidad.'}],
    'plantilla': 'feature',
    'documento': 'OUT/09-features/F02-bases-de-datos/0.1-indice-databasecontroller-manager-modelo-collab-database-layouts-template-appflo.md',
    'metricas': {'archivos': len(files), 'por_capa': {'ui': len([f for f in files if f['capa']=='ui'])}, 'por_fuente': {'appflowy': len(files)}},
    'prioridad': 2, 'concurrencia': 'paralela',
    'generado_en': '2026-10-19T21:42:00Z',
}

Path('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units/F02.0.1.json').write_text(json.dumps(unit, indent=2, ensure_ascii=False))
print('Wrote F02.0.1.json with', len(files), 'files')