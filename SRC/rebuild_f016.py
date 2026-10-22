"""Rebuild F01.6.json with EXACT F01.6 patterns (no cross-feature leaks)."""
import csv, json
from datetime import datetime, timezone

cov_path = '/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv'
unit_path = '/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units/F01.6.json'

# Exact patterns for F01.6 only (NOT base/, block_transaction_handler/, parsers/, etc.)
patterns = [
    'editor_plugins/slash_menu/',
    'editor_plugins/block_menu/',
    'editor_plugins/context_menu/',
    'editor_plugins/actions/',
    'editor_plugins/desktop_toolbar/',
    'editor_plugins/mobile_toolbar_v3/',
    'editor_plugins/mobile_floating_toolbar/',
    'editor_plugins/toolbar_item/',
    'editor_plugins/shortcuts/',
    'editor_plugins/find_and_replace/',
    'editor_plugins/keyboard_interceptor/',
    'editor_plugins/copy_and_paste/',
    'editor_plugins/undo_redo_toolbar_item.dart',
    'editor_plugins/exit_edit_mode_command.dart',
    'editor_plugins/align_toolbar_item/',
]

archivos = []
with open(cov_path) as f:
    for row in csv.DictReader(f):
        if row['feature_ids'] != 'F01':
            continue
        if '/editor_plugins/' not in row['ruta']:
            continue
        for p in patterns:
            if p in row['ruta']:
                archivos.append({
                    'fuente': row['fuente'],
                    'ruta': row['ruta'],
                    'capa': row['capa'],
                    'estado': row['estado'],
                })
                break

seen = set()
unique = []
for a in archivos:
    if a['ruta'] not in seen:
        seen.add(a['ruta'])
        unique.append(a)

print(f'Total matches: {len(archivos)}, Unique: {len(unique)}')

unit = {
    'schema_version': 1,
    'id': 'F01.6',
    'feature_id': 'F01',
    'sub_index': 6,
    'titulo': 'Interaccion: slash_menu, block_menu, context_menu, actions, toolbars, shortcuts, find_and_replace, copy_and_paste',
    'fuentes': ['appflowy'],
    'archivos': unique,
    'archivos_total': len(unique),
    'catalogos': ['events.json', 'protobuf.json', 'blocs.json', 'notifications.json', 'deps.json', 'misc.json'],
    'catalogos_razon': {
        'events.json': 'Eventos FFI dispatch',
        'protobuf.json': 'Entidades protobuf',
        'blocs.json': 'BLoCs del feature',
        'notifications.json': 'Notificaciones',
        'deps.json': 'Dependencias workspace',
        'misc.json': 'i18n keys, rutas, atajos',
    },
    'dependencias': [
        {'id': 'F01.0', 'tipo': 'indice', 'nota': 'Documento indice F01.0 debe existir antes de esta sub-unidad.'},
    ],
    'plantilla': 'feature',
    'documento': 'OUT/09-features/F01-documentos-y-editor/6-interaccion-slash-menu-block-menu-context-menu-actions-toolbars-shortcuts-find-and-replace-copy-and-paste.md',
    'metricas': {
        'archivos': len(unique),
        'por_capa': {'ui': len(unique)},
        'por_fuente': {'appflowy': len(unique)},
    },
    'prioridad': 2,
    'concurrencia': 'paralela',
    'generado_en': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
}

with open(unit_path, 'w') as f:
    json.dump(unit, f, indent=2, ensure_ascii=False)
print(f'Wrote {len(unique)} archivos')
# Verify by subfolder
from collections import Counter
c = Counter()
for a in unique:
    rel = a['ruta'].split('editor_plugins/')[1].split('/')[0]
    c[rel] += 1
for k, v in c.most_common():
    print(f'  {v:3} {k}')