import re, json
from pathlib import Path
doc_path = Path('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/09-features/F01-documentos-y-editor/8-infraestructura-del-editor-transaction-handler-block-transaction-handler-migrati.md')
text = doc_path.read_text()
inv = json.load(open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/inventario.json'))
files = inv.get('files', [])
basename_to_paths = {}
for entry in files:
    base = entry['ruta_rel'].split('/')[-1]
    basename_to_paths.setdefault(base, []).append((entry['fuente'], entry['ruta_rel']))
pattern = re.compile(r"`(?P<fname>[a-zA-Z0-9_./\-]+\.(?:rs|dart))(?::(?P<line>\d+)(?:[–-](?P<fin>\d+))?)?`")
def replace(m):
    fname = m.group('fname'); line = m.group('line'); fin = m.group('fin')
    if ':' in fname.split('.')[0] or fname.startswith(('editor/', 'collab/')):
        return m.group(0)
    base = fname.split('/')[-1]
    candidates = basename_to_paths.get(base, [])
    if not candidates:
        return m.group(0)
    matched = [c for c in candidates if c[0] == 'appflowy']
    fuen, ruta = matched[0] if matched else candidates[0]
    out = f"`{fuen}:{ruta}"
    if line: out += f":{line}"
    if fin: out += f"–{fin}"
    out += '`'
    return out
new = pattern.sub(replace, text)
new = re.sub(r'`appflowy:appflowy/', '`appflowy/', new)
new = re.sub(r':(\d+)\s+(\d+)\b', r':\1–\2', new)
doc_path.write_text(new)
print('OK')