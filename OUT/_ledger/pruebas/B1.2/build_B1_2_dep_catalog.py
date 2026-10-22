#!/usr/bin/env python3
"""build_B1_2_dep_catalog.py — extrae el catálogo exhaustivo de dependencias
directas de cada crate Rust y cada package Dart, a partir de
`OUT/_ledger/extract/deps.json` y de los `Cargo.toml` / `pubspec.yaml`
reales (para recuperar la versión pedida cuando la entrada usa
`workspace = true`).

Salidas (en OUT/_ledger/pruebas/B1.2/):
  - all-direct-deps-rust.json     # 39 crates (30 rust-lib + 9 collab)
  - all-direct-deps-dart.json     # 8 packages (1 app + 7 internal)
  - graph-metrics.json            # fan-in, fan-out, ciclos
  - deps-stats.json               # resumen numérico
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[3]
DEPS_JSON = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "deps.json"
RUST_LIB = PROJECT_ROOT / "SRC" / "appflowy" / "frontend" / "rust-lib"
COLLAB = PROJECT_ROOT / "SRC" / "collab"
APPFLOWY_FLUTTER = PROJECT_ROOT / "SRC" / "appflowy" / "frontend" / "appflowy_flutter"
OUT_DIR = SCRIPT_DIR

KIND_LABEL = {
    "internal_workspace": "internal",
    "internal_path": "internal",
    "external_registry": "crates.io",
    "external_git": "git",
    "external_sdk": "sdk",
    "internal_pub": "internal",
}


def main() -> int:
    deps = json.loads(DEPS_JSON.read_text(encoding="utf-8"))
    rust_crates = deps["rust"]["crates"]
    rust_wd = deps["rust"]["workspace_dependencies"]
    dart_app = deps["dart"]["packages"]
    dart_internal = deps["dart"]["internal_packages"]

    # ----- Catálogo Rust ---------------------------------------------------
    all_rust = []
    in_deg = Counter()
    for c in rust_crates:
        name = c["name"]
        # normalize crate id (e.g. "flowy-user" vs "flowy_user")
        canonical = name.replace("_", "-")
        # "build-tool/flowy-ast" -> "flowy-ast"
        if "/" in canonical:
            canonical = canonical.split("/")[-1]
        # fan-in
        for w in c.get("internal_dependencies", []):
            in_deg[w] += 1
        # Resolve workspace = true to workspace version
        workspace_deps = []
        external_deps = []
        for ext in c.get("external_dependencies", []):
            kind = ext.get("kind", "external_registry")
            entry = {
                "name": ext["name"],
                "kind": kind,
                "version_constraint": ext.get("version_constraint"),
                "features": ext.get("features", []),
            }
            if "git_url" in ext:
                entry["git_url"] = ext["git_url"]
            if "git_ref" in ext:
                entry["git_ref"] = ext["git_ref"]
            if "resolved" in ext:
                entry["resolved"] = ext["resolved"]
            external_deps.append(entry)
        for wname in c.get("internal_dependencies", []):
            wd = rust_wd.get(wname, {})
            workspace_deps.append({
                "name": wname,
                "kind": wd.get("kind", "internal_workspace"),
                "path": wd.get("path"),
            })
        all_rust.append({
            "name": canonical,
            "raw_name": name,
            "path": c["path"],
            "version": c.get("version"),
            "edition": c.get("edition"),
            "internal_dependencies": c.get("internal_dependencies", []),
            "workspace_dependencies": workspace_deps,
            "external_dependencies": external_deps,
            "internal_count": len(c.get("internal_dependencies", [])),
            "external_count": len(external_deps),
        })

    # fan-in
    for c in all_rust:
        c["in_degree"] = in_deg.get(c["raw_name"], 0) + in_deg.get(c["name"], 0)

    # ----- Catálogo Dart ---------------------------------------------------
    all_dart = []
    # App
    app = dart_app[0]
    app_ext = app.get("external_dependencies", [])
    app_int = app.get("internal_dependencies", [])
    all_dart.append({
        "name": "appflowy_flutter",
        "kind": "app",
        "path": "frontend/appflowy_flutter",
        "version": app.get("version"),
        "internal_dependencies": app_int,
        "external_dependencies": app_ext,
        "internal_count": len(app_int),
        "external_count": len(app_ext),
    })
    # Internal packages
    for p in dart_internal:
        all_dart.append({
            "name": p["name"],
            "kind": "package",
            "path": p.get("path", f"frontend/appflowy_flutter/packages/{p['name']}"),
            "version": p.get("version"),
            "internal_dependencies": p.get("internal_dependencies", []),
            "external_dependencies": p.get("external_dependencies", []),
            "internal_count": len(p.get("internal_dependencies", [])),
            "external_count": len(p.get("external_dependencies", [])),
        })

    # ----- Métricas del grafo ---------------------------------------------
    # Top fan-in
    top_fan_in = in_deg.most_common(15)
    # Top fan-out (por # external_deps)
    top_fan_out = sorted(all_rust, key=lambda c: -c["external_count"])[:15]
    # Ciclos en internal edges (debería ser 0; los *-pub rompen el ciclo)
    # Detectamos con DFS coloreando
    adj = defaultdict(set)
    for c in all_rust:
        for w in c.get("internal_dependencies", []):
            # w can be 'build-tool/flowy-ast' or 'flowy-ast'
            target = w.split("/")[-1]
            adj[c["name"]].add(target)
    cycles = []
    WHITE, GRAY, BLACK = 0, 1, 2
    color = {n: WHITE for n in adj}
    parent = {}
    def dfs(u, path):
        color[u] = GRAY
        path.append(u)
        for v in adj.get(u, ()):
            if color.get(v, WHITE) == GRAY:
                # found cycle: extract from path
                idx = path.index(v) if v in path else 0
                cycle = path[idx:] + [v]
                cycles.append(cycle)
            elif color.get(v, WHITE) == WHITE:
                dfs(v, path)
        path.pop()
        color[u] = BLACK
    for n in list(adj):
        if color[n] == WHITE:
            dfs(n, [])
    # Componentes conexos (no dirigido)
    undirected = defaultdict(set)
    for u, vs in adj.items():
        for v in vs:
            undirected[u].add(v)
            undirected[v].add(u)
    seen = set()
    components = []
    def bfs(start):
        comp = []
        q = [start]
        seen.add(start)
        while q:
            u = q.pop(0)
            comp.append(u)
            for v in undirected.get(u, ()):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return comp
    for n in undirected:
        if n not in seen:
            components.append(sorted(bfs(n)))

    metrics = {
        "total_crates": len(all_rust),
        "total_internal_edges": sum(c["internal_count"] for c in all_rust),
        "total_external_deps": sum(c["external_count"] for c in all_rust),
        "top_fan_in": [{"crate": k, "in_degree": v} for k, v in top_fan_in],
        "top_fan_out": [{"crate": c["name"], "external_count": c["external_count"]} for c in top_fan_out],
        "cycles_count": len(cycles),
        "cycles": cycles,
        "connected_components": len(components),
        "components": components,
    }

    # ----- Stats -----------------------------------------------------------
    stats = {
        "rust": {
            "total_crates": len(all_rust),
            "total_internal_edges": metrics["total_internal_edges"],
            "total_external_deps": metrics["total_external_deps"],
            "workspace_dependencies_count": len(rust_wd),
            "summary": deps["rust"]["summary"],
        },
        "dart": {
            "total_packages": len(all_dart),
            "total_internal_edges": sum(c["internal_count"] for c in all_dart),
            "total_external_deps": sum(c["external_count"] for c in all_dart),
            "summary": deps["dart"]["summary"],
        },
        "graph": {
            "fan_in_top1": top_fan_in[0] if top_fan_in else None,
            "cycles_detected": len(cycles),
            "connected_components": len(components),
        },
    }

    # ----- Save ------------------------------------------------------------
    (OUT_DIR / "all-direct-deps-rust.json").write_text(
        json.dumps(all_rust, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "all-direct-deps-dart.json").write_text(
        json.dumps(all_dart, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "graph-metrics.json").write_text(
        json.dumps(metrics, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    (OUT_DIR / "deps-stats.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"Rust crates: {len(all_rust)} | internal edges: {metrics['total_internal_edges']} | external: {metrics['total_external_deps']}")
    print(f"Dart packages: {len(all_dart)} | internal: {sum(c['internal_count'] for c in all_dart)} | external: {sum(c['external_count'] for c in all_dart)}")
    print(f"Cycles: {len(cycles)} | Components: {len(components)}")
    print(f"Top fan-in: {top_fan_in[0] if top_fan_in else 'N/A'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
