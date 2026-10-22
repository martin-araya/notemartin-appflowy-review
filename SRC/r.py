import json
p = '/Users/martin/Desktop/projects/Skills/notemarin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units/F01.9.json'
import json
p = '/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units/F01.9.json'
u = json.load(open(p))
u['documento'] = 'OUT/09-features/F01-documentos-y-editor/9-ia-en-el-editor-editor-plugins-ai-ai-writer-completion-enlaza-con-f09.md'
json.dump(u, open(p, 'w'), indent=2, ensure_ascii=False)
print('OK')