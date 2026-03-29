#!/usr/bin/env python3
"""Architecture Intelligence — AST-based module scanner for SMA Research Platform.

Walks all Python files under src/sma_platform/ and generates 4 JSON artifacts
in docs/architecture/:
  1. module-map.json     — modules with imports, classes, functions, categories
  2. endpoint-map.json   — FastAPI endpoints with path, method, handler, docstring
  3. call-graph.json     — internal cross-module import graph
  4. db-table-map.json   — SQL table references per module

Usage:
    python scripts/generate_module_map.py
"""

from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Resolve project root (parent of scripts/)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
SRC_ROOT = PROJECT_ROOT / "src" / "sma_platform"
DOCS_DIR = PROJECT_ROOT / "docs" / "architecture"

# ---------------------------------------------------------------------------
# Category detection
# ---------------------------------------------------------------------------
CATEGORY_RULES: list[tuple[str, str]] = [
    ("api/routes/", "api"),
    ("api/", "api"),
    ("reasoning/", "reasoning"),
    ("ingestion/", "ingestion"),
    ("agents/", "agents"),
    ("core/", "core"),
    ("gpu/", "gpu"),
    ("scripts/", "scripts"),
    ("ucm/", "ucm"),
]


def categorize(rel_path: str) -> str:
    """Return a category string based on the relative path within src/sma_platform/."""
    for prefix, cat in CATEGORY_RULES:
        if rel_path.startswith(prefix):
            return cat
    return "other"


# ---------------------------------------------------------------------------
# FastAPI decorator patterns
# ---------------------------------------------------------------------------
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "options", "head"}


# APIRouter(prefix="/foo")
ROUTER_PREFIX_RE = re.compile(r'APIRouter\s*\([^)]*prefix\s*=\s*["\']([^"\']*)["\']')


# ---------------------------------------------------------------------------
# SQL table detection
# ---------------------------------------------------------------------------
SQL_TABLE_RE = re.compile(
    r"\b(?:CREATE\s+TABLE|INSERT\s+INTO|SELECT\s+.*?\bFROM|UPDATE|DELETE\s+FROM|JOIN|LEFT\s+JOIN|RIGHT\s+JOIN|INNER\s+JOIN|CROSS\s+JOIN|FULL\s+JOIN)\s+"
    r"(?:IF\s+NOT\s+EXISTS\s+)?\"?(\w+)\"?",
    re.IGNORECASE,
)

# Tables to ignore (SQL keywords that look like table names)
IGNORE_TABLES = {
    "set", "select", "where", "and", "or", "not", "null", "true", "false",
    "values", "as", "on", "order", "by", "group", "having", "limit", "offset",
    "case", "when", "then", "else", "end", "in", "is", "like", "between",
    "exists", "all", "any", "some", "union", "except", "intersect",
    "distinct", "into", "from", "join", "left", "right", "inner", "outer",
    "cross", "full", "natural", "using", "constraint", "primary", "foreign",
    "key", "references", "index", "unique", "check", "default", "create",
    "table", "alter", "drop", "insert", "update", "delete", "with",
    "recursive", "lateral", "returning", "cascade", "restrict", "no",
    "action", "current_timestamp", "now", "coalesce", "unnest",
}


def extract_tables_from_source(source: str) -> list[str]:
    """Find SQL table names referenced in Python source code."""
    tables: set[str] = set()
    for match in SQL_TABLE_RE.finditer(source):
        name = match.group(1).lower().strip('"').strip("'")
        if name and name not in IGNORE_TABLES and not name.startswith("$"):
            tables.add(name)
    return sorted(tables)


# ---------------------------------------------------------------------------
# AST-based extraction
# ---------------------------------------------------------------------------

def extract_endpoint_info(node: ast.FunctionDef) -> list[dict]:
    """Extract FastAPI endpoint info from a decorated function."""
    endpoints: list[dict] = []
    for dec in node.decorator_list:
        # Handle @router.get("/path") and @app.get("/path")
        if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
            method_name = dec.func.attr.lower()
            if method_name not in HTTP_METHODS:
                continue
            # Extract path from first positional arg
            path = ""
            if dec.args and isinstance(dec.args[0], ast.Constant):
                path = dec.args[0].value
            # Extract docstring
            docstring = ast.get_docstring(node) or ""
            endpoints.append({
                "path": path,
                "method": method_name.upper(),
                "handler": node.name,
                "docstring": docstring[:200] if docstring else "",
                "line": node.lineno,
            })
    return endpoints


def extract_router_prefix(tree: ast.Module) -> str:
    """Find APIRouter(prefix=...) in module."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id == "APIRouter":
                for kw in node.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        return kw.value.value
            elif isinstance(func, ast.Attribute) and func.attr == "APIRouter":
                for kw in node.keywords:
                    if kw.arg == "prefix" and isinstance(kw.value, ast.Constant):
                        return kw.value.value
    return ""


def extract_imports(tree: ast.Module, module_rel_path: str) -> list[str]:
    """Extract internal (sma_platform) imports as relative module paths."""
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if "sma_platform" in alias.name:
                    imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and "sma_platform" in node.module:
                imports.append(node.module)
            elif node.level and node.level > 0:
                # Relative import — resolve to a module path
                parts = module_rel_path.replace("\\", "/").split("/")
                # Remove the filename
                package_parts = parts[:-1]
                # Go up `level` directories
                level = node.level
                if level <= len(package_parts):
                    base = package_parts[:len(package_parts) - level + 1]
                else:
                    base = []
                if node.module:
                    base_path = ".".join(base + node.module.split(".")) if base else node.module
                else:
                    base_path = ".".join(base) if base else ""
                if base_path:
                    full = f"sma_platform.{base_path}" if not base_path.startswith("sma_platform") else base_path
                    imports.append(full)
    return sorted(set(imports))


def extract_classes(tree: ast.Module) -> list[dict]:
    """Extract class definitions with their methods."""
    classes = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    methods.append(item.name)
            classes.append({
                "name": node.name,
                "methods": methods,
                "line": node.lineno,
            })
    return classes


def extract_functions(tree: ast.Module) -> list[dict]:
    """Extract top-level function definitions."""
    functions = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node) or ""
            functions.append({
                "name": node.name,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "line": node.lineno,
                "docstring": docstring[:150] if docstring else "",
            })
    return functions


# ---------------------------------------------------------------------------
# include_router prefix resolution
# ---------------------------------------------------------------------------

def extract_include_router_prefixes(app_source: str) -> dict[str, str]:
    """Parse app.py to find include_router(X.router, prefix=...) mappings.

    Returns dict mapping module variable name to the prefix used in include_router.
    e.g. {"targets": "/api/v2", "comparative": "/api/v2/comparative"}
    """
    prefixes: dict[str, str] = {}
    pattern = re.compile(
        r'include_router\(\s*(\w+)\.router\s*,\s*prefix\s*=\s*["\']([^"\']*)["\']'
    )
    for m in pattern.finditer(app_source):
        module_name = m.group(1)
        prefix = m.group(2)
        prefixes[module_name] = prefix
    return prefixes


# ---------------------------------------------------------------------------
# Main scanning logic
# ---------------------------------------------------------------------------

def scan_file(filepath: Path, rel_to_src: str) -> dict | None:
    """Parse a single Python file and extract all metadata."""
    try:
        source = filepath.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        print(f"  WARN: Cannot read {filepath}: {e}", file=sys.stderr)
        return None

    line_count = source.count("\n") + 1

    try:
        tree = ast.parse(source, filename=str(filepath))
    except SyntaxError as e:
        print(f"  WARN: Syntax error in {filepath}: {e}", file=sys.stderr)
        return {
            "file": rel_to_src,
            "category": categorize(rel_to_src),
            "line_count": line_count,
            "imports": [],
            "classes": [],
            "functions": [],
            "endpoints": [],
            "tables": extract_tables_from_source(source),
            "parse_error": str(e),
        }

    category = categorize(rel_to_src)
    imports = extract_imports(tree, rel_to_src)
    classes = extract_classes(tree)
    functions = extract_functions(tree)

    # Endpoints
    endpoints: list[dict] = []
    router_prefix = extract_router_prefix(tree)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            eps = extract_endpoint_info(node)
            for ep in eps:
                if router_prefix and not ep["path"].startswith(router_prefix):
                    ep["router_prefix"] = router_prefix
            endpoints.extend(eps)

    # SQL tables
    tables = extract_tables_from_source(source)

    return {
        "file": rel_to_src,
        "category": category,
        "line_count": line_count,
        "imports": imports,
        "classes": classes,
        "functions": functions,
        "endpoints": endpoints,
        "tables": tables,
    }


def build_imported_by(modules: list[dict]) -> dict[str, list[str]]:
    """Build a reverse lookup: for each module, who imports it."""
    file_to_dotted: dict[str, str] = {}
    for mod in modules:
        dotted = mod["file"].replace("/", ".").replace("\\", ".").removesuffix(".py")
        if dotted.endswith(".__init__"):
            dotted = dotted.removesuffix(".__init__")
        dotted = f"sma_platform.{dotted}" if not dotted.startswith("sma_platform") else dotted
        file_to_dotted[mod["file"]] = dotted

    dotted_to_file: dict[str, str] = {v: k for k, v in file_to_dotted.items()}

    imported_by: dict[str, list[str]] = {mod["file"]: [] for mod in modules}

    for mod in modules:
        for imp in mod.get("imports", []):
            target_file = dotted_to_file.get(imp)
            if not target_file:
                for dotted, fpath in dotted_to_file.items():
                    if imp.startswith(dotted) or dotted.startswith(imp):
                        target_file = fpath
                        break
            if target_file and target_file in imported_by:
                if mod["file"] not in imported_by[target_file]:
                    imported_by[target_file].append(mod["file"])

    return imported_by


def build_call_graph(modules: list[dict]) -> dict:
    """Build call graph as {source_file: [target_files]}."""
    file_to_dotted: dict[str, str] = {}
    for mod in modules:
        dotted = mod["file"].replace("/", ".").replace("\\", ".").removesuffix(".py")
        if dotted.endswith(".__init__"):
            dotted = dotted.removesuffix(".__init__")
        dotted = f"sma_platform.{dotted}" if not dotted.startswith("sma_platform") else dotted
        file_to_dotted[mod["file"]] = dotted

    dotted_to_file: dict[str, str] = {v: k for k, v in file_to_dotted.items()}

    graph: dict[str, list[str]] = {}
    for mod in modules:
        targets: list[str] = []
        for imp in mod.get("imports", []):
            target_file = dotted_to_file.get(imp)
            if not target_file:
                for dotted, fpath in dotted_to_file.items():
                    if imp.startswith(dotted) or dotted.startswith(imp):
                        target_file = fpath
                        break
            if target_file and target_file != mod["file"]:
                if target_file not in targets:
                    targets.append(target_file)
        if targets:
            graph[mod["file"]] = sorted(targets)

    return graph


def main() -> None:
    print(f"SMA Architecture Intelligence Scanner")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Source root:   {SRC_ROOT}")
    print()

    if not SRC_ROOT.exists():
        print(f"ERROR: Source root not found: {SRC_ROOT}", file=sys.stderr)
        sys.exit(1)

    # Create output directory
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    # Find all Python files
    py_files = sorted(SRC_ROOT.rglob("*.py"))
    print(f"Found {len(py_files)} Python files")

    # Scan each file
    modules: list[dict] = []
    total_endpoints = 0
    total_tables: set[str] = set()
    errors = 0

    for filepath in py_files:
        if "__pycache__" in str(filepath):
            continue

        rel_path = str(filepath.relative_to(SRC_ROOT)).replace("\\", "/")
        result = scan_file(filepath, rel_path)
        if result:
            if "parse_error" in result:
                errors += 1
            modules.append(result)
            total_endpoints += len(result.get("endpoints", []))
            total_tables.update(result.get("tables", []))

    # Build imported_by reverse lookup
    imported_by = build_imported_by(modules)
    for mod in modules:
        mod["imported_by"] = imported_by.get(mod["file"], [])

    # Build category counts
    category_counts: dict[str, int] = {}
    for mod in modules:
        cat = mod["category"]
        category_counts[cat] = category_counts.get(cat, 0) + 1

    # Read app.py include_router prefixes
    app_py = SRC_ROOT / "api" / "app.py"
    include_prefixes: dict[str, str] = {}
    if app_py.exists():
        include_prefixes = extract_include_router_prefixes(
            app_py.read_text(encoding="utf-8", errors="replace")
        )

    # -----------------------------------------------------------------------
    # 1. module-map.json
    # -----------------------------------------------------------------------
    module_map = {
        "generated": "auto",
        "scanner": "scripts/generate_module_map.py",
        "total_modules": len(modules),
        "total_lines": sum(m["line_count"] for m in modules),
        "categories": category_counts,
        "modules": modules,
    }

    out_path = DOCS_DIR / "module-map.json"
    out_path.write_text(json.dumps(module_map, indent=2, default=str), encoding="utf-8")
    print(f"\n  module-map.json: {len(modules)} modules, {module_map['total_lines']} lines")

    # -----------------------------------------------------------------------
    # 2. endpoint-map.json
    # -----------------------------------------------------------------------
    all_endpoints: list[dict] = []
    for mod in modules:
        for ep in mod.get("endpoints", []):
            full_path = ep["path"]
            file_stem = Path(mod["file"]).stem
            app_prefix = include_prefixes.get(file_stem, "")
            router_prefix = ep.pop("router_prefix", "")

            # Build full path: app_prefix + router_prefix + endpoint_path
            # e.g. /api/v2 + /advisory + /pack = /api/v2/advisory/pack
            parts = []
            if app_prefix:
                parts.append(app_prefix.rstrip("/"))
            if router_prefix:
                parts.append(router_prefix.strip("/"))
            if full_path:
                parts.append(full_path.lstrip("/"))
            full_path = "/".join(parts) if parts else "/"
            if not full_path.startswith("/"):
                full_path = "/" + full_path

            all_endpoints.append({
                "full_path": full_path,
                "method": ep["method"],
                "handler": ep["handler"],
                "file": mod["file"],
                "line": ep["line"],
                "docstring": ep["docstring"],
            })

    endpoint_map = {
        "generated": "auto",
        "total_endpoints": len(all_endpoints),
        "endpoints": sorted(all_endpoints, key=lambda e: (e["full_path"], e["method"])),
    }

    out_path = DOCS_DIR / "endpoint-map.json"
    out_path.write_text(json.dumps(endpoint_map, indent=2, default=str), encoding="utf-8")
    print(f"  endpoint-map.json: {len(all_endpoints)} endpoints")

    # -----------------------------------------------------------------------
    # 3. call-graph.json
    # -----------------------------------------------------------------------
    call_graph = build_call_graph(modules)

    call_graph_out = {
        "generated": "auto",
        "description": "Internal cross-module import graph (source -> [targets])",
        "total_edges": sum(len(v) for v in call_graph.values()),
        "graph": call_graph,
    }

    out_path = DOCS_DIR / "call-graph.json"
    out_path.write_text(json.dumps(call_graph_out, indent=2, default=str), encoding="utf-8")
    print(f"  call-graph.json: {len(call_graph)} source modules, {call_graph_out['total_edges']} edges")

    # -----------------------------------------------------------------------
    # 4. db-table-map.json
    # -----------------------------------------------------------------------
    table_to_modules: dict[str, list[str]] = {}
    module_to_tables: dict[str, list[str]] = {}

    for mod in modules:
        tables = mod.get("tables", [])
        if tables:
            module_to_tables[mod["file"]] = tables
            for t in tables:
                if t not in table_to_modules:
                    table_to_modules[t] = []
                if mod["file"] not in table_to_modules[t]:
                    table_to_modules[t].append(mod["file"])

    db_table_map = {
        "generated": "auto",
        "total_tables": len(table_to_modules),
        "table_to_modules": dict(sorted(table_to_modules.items())),
        "module_to_tables": dict(sorted(module_to_tables.items())),
    }

    out_path = DOCS_DIR / "db-table-map.json"
    out_path.write_text(json.dumps(db_table_map, indent=2, default=str), encoding="utf-8")
    print(f"  db-table-map.json: {len(table_to_modules)} tables across {len(module_to_tables)} modules")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Modules scanned:  {len(modules)}")
    print(f"  Total lines:      {module_map['total_lines']}")
    print(f"  Endpoints:        {len(all_endpoints)}")
    print(f"  DB tables:        {len(table_to_modules)}")
    print(f"  Call graph edges:  {call_graph_out['total_edges']}")
    print(f"  Parse errors:     {errors}")
    print(f"\n  Categories:")
    for cat, count in sorted(category_counts.items()):
        print(f"    {cat:15s} {count:4d} modules")
    print(f"\n  Output: {DOCS_DIR}/")
    print(f"  Done.")


if __name__ == "__main__":
    main()
