#!/usr/bin/env python3
"""Generate docs/MODULE-MAP.md from every module.spec.md in the seven repos (SAN-1627).

The specs are the source; this page is never edited by hand. It holds:
  - a repo-level dependency diagram (Mermaid), drawn from module-to-module references;
  - the cross-repo module edges behind that diagram;
  - which modules read each tenant feature flag;
  - the module inventory per repo;
  - gaps: module folders without a spec, and specs whose front matter is not valid YAML.

Edges come from the specs' front matter. Any string that names another repo's path
(e.g. "sc-saas-backend/src/modules/users/...") links to the module whose folder that path is in.
Frontend `backend_modules` entries written as "users (PATCH api/v1/...)" link by module name.
Fields named *consumer* / consumed_by point the other way (the named module depends on this one).

Usage (from the workspace root, with the seven repos checked out next to each other):
  python3 scripts/generate-module-map.py            # write docs/MODULE-MAP.md
  python3 scripts/generate-module-map.py --check    # exit 1 if the committed page is out of date
Needs PyYAML.
"""
import os
import re
import subprocess
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "MODULE-MAP.md")
ORG_URL = "https://github.com/sanchiconnect-org"
BRANCH = "ai_native_setup"

# repo, short name, folders whose direct children are modules
REPOS = [
    ("sanchiconnect-saas-tenants", "tenants", ["src/modules"]),
    ("sc-saas-backend", "backend", ["src/modules"]),
    ("sc-saas-frontend", "frontend", ["src/app/modules"]),
    ("sc-saas-admin", "admin", ["modules"]),
    ("sanchiconnect-saas-tenants-admin", "tenants-admin", ["modules"]),
    ("ai-startups-analyzer", "analyzer", ["api"]),
    ("sc-saas-3rdparty-webservices", "webservices", ["src/modules"]),
]
SHORT = {r: s for r, s, _ in REPOS}
REPO_RE = re.compile(r"(sanchiconnect-saas-tenants-admin|sanchiconnect-saas-tenants|sc-saas-backend|sc-saas-frontend|"
                     r"sc-saas-admin|ai-startups-analyzer|sc-saas-3rdparty-webservices)/([\w./-]*)")
REVERSE_KEYS = ("consumer", "consumed_by")


def git_files(repo):
    out = subprocess.run(["git", "-C", os.path.join(ROOT, repo), "ls-files"], capture_output=True, text=True, check=True)
    return out.stdout.split()


def strings(value, key=""):
    """Yield (key, string) for every string in a parsed YAML value, keeping the top-level key."""
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for k, v in value.items():
            field = key or str(k)
            if isinstance(k, str):
                yield from strings(k, field)
            yield from strings(v, field)
    elif isinstance(value, list):
        for v in value:
            yield from strings(v, key)


def first_token(text):
    m = re.match(r"\s*([a-z][a-z0-9_]*)", text)
    return m.group(1) if m else None


def tenant_flags():
    path = os.path.join(ROOT, "sanchiconnect-saas-tenants/src/modules/tenants/entities/tenant-users.entity.ts")
    src = open(path, encoding="utf-8").read()
    flags = set()
    for chunk in src.split("@Column(")[1:]:
        body = chunk.split(")", 1)[0]
        name = re.search(r"name:\s*'([a-z0-9_]+)'", body)
        if name and re.search(r"type:\s*'boolean'|'tinyint'|'boolean'", body):
            flags.add(name.group(1))
    return flags


def load():
    modules = {}          # (repo, folder) -> info
    folders = defaultdict(set)   # repo -> module folders that exist
    tracked = {}          # repo -> every tracked file
    for repo, short, roots in REPOS:
        files = git_files(repo)
        tracked[repo] = files
        for f in files:
            for root in roots:
                if f.startswith(root + "/"):
                    rest = f[len(root) + 1:].split("/")
                    if len(rest) > 1:
                        folders[repo].add(root + "/" + rest[0])
        for f in sorted(files):
            if not f.endswith("module.spec.md"):
                continue
            folder = os.path.dirname(f)
            text = open(os.path.join(ROOT, repo, f), encoding="utf-8").read()
            m = re.match(r"---\n(.*?)\n---", text, re.S)
            raw = m.group(1) if m else ""
            data, error = {}, None
            try:
                data = yaml.safe_load(raw) or {} if m else {}
                if not isinstance(data, dict):
                    data, error = {}, "front matter is not a mapping"
            except yaml.YAMLError as e:
                error = str(e).splitlines()[0]
            if not m:
                error = "no front matter"
            modules[(repo, folder)] = {
                "repo": repo, "folder": folder, "spec": f, "raw": raw, "data": data, "error": error,
                "name": str(data.get("module") or os.path.basename(folder) or repo),
            }
    return modules, folders, tracked


def resolve(path_repo, path, modules):
    """The module whose folder contains path_repo/path (longest folder wins)."""
    best = None
    for (repo, folder) in modules:
        if repo != path_repo:
            continue
        if folder == "" or path == folder or path.startswith(folder + "/"):
            if best is None or len(folder) > len(best[1]):
                best = (repo, folder)
    return best


def build(modules, flags, tracked):
    edges = defaultdict(set)      # (from, to) -> fields
    flag_use = defaultdict(lambda: defaultdict(set))   # flag -> repo -> module names
    stale = set()         # (referring repo, spec, referenced repo/path) for paths that don't exist
    backend_by_name = {os.path.basename(f): (r, f) for (r, f) in modules if r == "sc-saas-backend"}
    for key, mod in list(modules.items()):
        if mod["spec"] is None:
            continue
        data = mod["data"]
        pairs = list(strings(data)) if data else [("", mod["raw"])]
        for field, text in pairs:
            for repo, path in REPO_RE.findall(text):
                path = path.rstrip("/.")
                target = resolve(repo, path, modules)
                if not target and repo != mod["repo"]:
                    # no spec covers the path: keep the edge against the folder, so the repo link isn't lost
                    folder = "/".join(path.split("/")[:3]) or repo
                    exists = any(f == path or f.startswith(path + "/") for f in tracked[repo])
                    if not exists:
                        stale.add((mod["repo"], mod["spec"], f"{repo}/{path}"))
                    target = (repo, folder)
                    modules.setdefault(target, {"repo": repo, "folder": folder, "spec": None, "raw": "", "data": {},
                                                "error": None,
                                                "name": f"{folder} ({'no spec' if exists else 'path not found'})"})
                if not target or target == key:
                    continue
                edge = (target, key) if any(r in field for r in REVERSE_KEYS) else (key, target)
                edges[edge].add(field or "front matter")
            if field == "backend_modules" and mod["repo"] == "sc-saas-frontend":
                target = backend_by_name.get((first_token(text) or "").replace("_", "-")) or backend_by_name.get(first_token(text) or "")
                if target:
                    edges[(key, target)].add(field)
            if field in ("flags", "feature_flags") or field.endswith("flags"):
                token = first_token(text)
                if token in flags:
                    flag_use[token][mod["repo"]].add(mod["name"])
        for side in ("owns", "consumes"):
            for token in (data.get(side) or {}).get("flags") or [] if isinstance(data.get(side), dict) else []:
                token = first_token(str(token))
                if token in flags:
                    flag_use[token][mod["repo"]].add(mod["name"])
    return edges, flag_use, stale


def link(repo, path):
    return f"[{path}]({ORG_URL}/{repo}/blob/{BRANCH}/{path})"


def cell(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(modules, folders, edges, flag_use, flags, stale):
    out = ["# Module map", "",
           "_Generated by `scripts/generate-module-map.py` from every `module.spec.md` in the seven repos "
           f"(branch `{BRANCH}`). Do not edit by hand: fix the spec and regenerate (SAN-1627)._", "",
           "For each module's detail, follow its spec link or the repo's `specs/<repo>-module-specs-index.md`. "
           "The repo-level contracts and invariants are in `CLAUDE.md`.", ""]

    # summary
    out += ["## Summary", "", "| Repo | Specs | Module folders without a spec | Specs with unreadable front matter |",
            "|---|---|---|---|"]
    spec_folders = defaultdict(set)
    for (repo, folder), mod in modules.items():
        if mod["spec"]:
            spec_folders[repo].add(folder)
    missing = {repo: sorted(f for f in folders[repo] if f not in spec_folders[repo]) for repo, _, _ in REPOS}
    broken = defaultdict(list)
    for mod in modules.values():
        if mod["error"]:
            broken[mod["repo"]].append(mod)
    for repo, short, _ in REPOS:
        out.append(f"| {repo} | {len(spec_folders[repo])} | {len(missing[repo])} | {len(broken[repo])} |")
    out.append("")

    # repo diagram
    repo_edges = defaultdict(int)
    for (a, b) in edges:
        if a[0] != b[0]:
            repo_edges[(a[0], b[0])] += 1
    out += ["## Repo dependencies", "",
            "An arrow means modules in the first repo depend on modules in the second; the number is how many "
            "module-to-module references the specs record. Shared-database and HTTP edges are both counted.", "",
            "```mermaid", "graph LR"]
    for repo, short, _ in REPOS:
        out.append(f'    {short.replace("-", "_")}["{repo}"]')
    for (a, b), n in sorted(repo_edges.items()):
        out.append(f'    {SHORT[a].replace("-", "_")} -->|{n}| {SHORT[b].replace("-", "_")}')
    out += ["```", ""]

    # cross-repo edges
    out += ["## Cross-repo module dependencies", "", "| From | To | Recorded in |", "|---|---|---|"]
    rows = []
    for (a, b), fields in edges.items():
        if a[0] != b[0]:
            ma, mb = modules[a], modules[b]
            rows.append((SHORT[a[0]], ma["name"], SHORT[b[0]], mb["name"], ", ".join(sorted(fields))))
    for ra, na, rb, nb, f in sorted(rows):
        out.append(f"| {ra} / {cell(na)} | {rb} / {cell(nb)} | {cell(f)} |")
    out.append("")

    # flags
    out += ["## Feature flags by module", "",
            "Tenant flags (boolean columns of `TenantUsersEntity`) and the modules whose specs say they read them. "
            "A flag with no row here is read by no specced module, or the specs don't record it.", "",
            "| Flag | " + " | ".join(s for _, s, _ in REPOS) + " |", "|---|" + "---|" * len(REPOS)]
    for flag in sorted(flag_use):
        cols = [", ".join(sorted(flag_use[flag].get(r, []))) for r, _, _ in REPOS]
        out.append(f"| `{flag}` | " + " | ".join(cell(c) for c in cols) + " |")
    unused = sorted(flags - set(flag_use))
    out += ["", f"Flags no spec mentions ({len(unused)}): " + ", ".join(f"`{f}`" for f in unused), ""]

    # inventory
    out += ["## Module inventory", ""]
    for repo, short, _ in REPOS:
        mods = sorted((m for m in modules.values() if m["repo"] == repo and m["spec"]), key=lambda m: m["folder"])
        out += [f"### {repo}", "", "| Module | Status | Updated | Depends on (other repos) | Spec |", "|---|---|---|---|---|"]
        for m in mods:
            deps = sorted({f"{SHORT[b[0]]}/{modules[b]['name']}" for (a, b) in edges if a == (m["repo"], m["folder"]) and b[0] != repo})
            d = m["data"]
            out.append(f"| {cell(m['name'])} | {cell(d.get('status', '?'))} | {cell(d.get('updated', ''))} | "
                       f"{cell(', '.join(deps))} | {link(repo, m['spec'])} |")
        out.append("")

    # gaps
    out += ["## Gaps", "", "Write the missing spec, fix the front matter, or correct the path, the next time the module is touched.", ""]
    stale_by_repo = defaultdict(list)
    for repo, spec, ref in sorted(stale):
        stale_by_repo[repo].append((spec, ref))
    for repo, short, _ in REPOS:
        if not missing[repo] and not broken[repo] and not stale_by_repo[repo]:
            continue
        out.append(f"### {repo}")
        out.append("")
        for f in missing[repo]:
            out.append(f"- no spec: `{f}/`")
        for m in broken[repo]:
            out.append(f"- front matter not readable: {link(repo, m['spec'])} ({cell(m['error'])})")
        for spec, ref in stale_by_repo[repo]:
            out.append(f"- names a path that doesn't exist: {link(repo, spec)} → `{ref}`")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def main():
    for repo, _, _ in REPOS:
        if not os.path.isdir(os.path.join(ROOT, repo, ".git")):
            sys.exit(f"missing checkout: {repo} (clone the seven repos next to scripts/)")
    modules, folders, tracked = load()
    flags = tenant_flags()
    edges, flag_use, stale = build(modules, flags, tracked)
    page = render(modules, folders, edges, flag_use, flags, stale)
    if "--check" in sys.argv:
        current = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if current != page:
            sys.exit("docs/MODULE-MAP.md is out of date: run python3 scripts/generate-module-map.py")
        print("docs/MODULE-MAP.md is up to date")
        return
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    specs = sum(1 for m in modules.values() if m["spec"])
    print(f"wrote {os.path.relpath(OUT, ROOT)}: {specs} specs, {len(edges)} module edges, "
          f"{len(flag_use)} flags in use, {len(stale)} stale path references")


if __name__ == "__main__":
    main()
