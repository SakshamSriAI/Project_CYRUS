"""CYRUS Controlled Codebase Inspector.

Provides safe, sandboxed inspection of local project files, code structure,
symbol search (classes, functions, endpoints), and codebase metrics.

Strictly confined to CYRUS_SANDBOX_PATH.
Addresses the user as "Sir".
"""

import ast
from dataclasses import dataclass, field
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
from backend.app.config import settings
from backend.app.guardian.permissions import ActionRequest, permission_engine

logger = logging.getLogger("cyrus.research.code_inspector")

IGNORED_DIRECTORIES = {
    ".git", ".venv", "node_modules", "__pycache__", "dist", "build",
    ".pytest_cache", ".gemini", "coverage", ".idea", ".vscode",
}

IGNORED_EXTENSIONS = {
    ".pyc", ".pyo", ".pyd", ".onnx", ".bin", ".wav", ".mp3", ".db",
    ".sqlite", ".sqlite3", ".tar", ".gz", ".zip", ".DS_Store",
}


@dataclass
class CodeSymbol:
    """Represents an extracted code symbol (class, function, route, interface)."""
    name: str
    symbol_type: str  # class, function, async_function, route, interface, react_component
    file_path: str
    line_number: int
    signature: str
    docstring: Optional[str] = None


@dataclass
class FileTreeNode:
    """Hierarchical node for file tree representation."""
    name: str
    path: str
    node_type: str  # directory or file
    size_bytes: int = 0
    children: List["FileTreeNode"] = field(default_factory=list)


class CodebaseInspector:
    """Sandboxed code inspector for project files and symbols."""

    def __init__(self, sandbox_root: Optional[Path] = None, user_form_of_address: str = "Sir"):
        self.sandbox_root = (sandbox_root or Path(settings.CYRUS_SANDBOX_PATH)).resolve()
        self.form_of_address = user_form_of_address

    def is_safe_path(self, target_path_str: str) -> bool:
        """Verifies if target resides within sandbox root."""
        try:
            target = Path(target_path_str).resolve()
            return target == self.sandbox_root or self.sandbox_root in target.parents
        except Exception:
            return False

    def get_file_tree(self, subdir: str = "", max_depth: int = 3) -> Dict[str, Any]:
        """Generates a filtered directory tree starting from sandbox root or subdir."""
        target_dir = (self.sandbox_root / subdir).resolve()
        if not self.is_safe_path(str(target_dir)) or not target_dir.exists():
            return {
                "error": f"Target path is outside authorized sandbox or does not exist, {self.form_of_address}.",
                "tree": None,
            }

        def build_node(current_path: Path, current_depth: int) -> Optional[Dict[str, Any]]:
            if current_depth > max_depth:
                return None

            name = current_path.name or str(current_path)
            if name in IGNORED_DIRECTORIES or current_path.suffix in IGNORED_EXTENSIONS:
                return None

            try:
                rel = str(current_path.relative_to(self.sandbox_root))
            except Exception:
                rel = current_path.name

            if current_path.is_file():
                return {
                    "name": name,
                    "path": rel,
                    "type": "file",
                    "size_bytes": current_path.stat().st_size,
                    "extension": current_path.suffix,
                }

            # Directory
            children = []
            try:
                for entry in sorted(current_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                    if entry.name in IGNORED_DIRECTORIES or entry.name.startswith("."):
                        continue
                    child_node = build_node(entry, current_depth + 1)
                    if child_node is not None:
                        children.append(child_node)
            except PermissionError:
                pass

            return {
                "name": name,
                "path": rel if rel != "." else "",
                "type": "directory",
                "children": children,
            }

        tree_data = build_node(target_dir, 0)
        return {"tree": tree_data, "root": str(target_dir.relative_to(self.sandbox_root) if target_dir != self.sandbox_root else ".")}

    def _extract_python_symbols(self, file_path: Path, rel_path: str) -> List[CodeSymbol]:
        """Extracts AST symbols from Python files."""
        symbols: List[CodeSymbol] = []
        try:
            content = file_path.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(file_path))
        except Exception:
            return symbols

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        symbol_type="class",
                        file_path=rel_path,
                        line_number=node.lineno,
                        signature=f"class {node.name}",
                        docstring=doc,
                    )
                )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                stype = "async_function" if isinstance(node, ast.AsyncFunctionDef) else "function"

                # Check if it's a FastAPI route endpoint
                is_route = False
                route_method = ""
                for dec in node.decorator_list:
                    dec_str = ast.unparse(dec) if hasattr(ast, "unparse") else ""
                    if any(m in dec_str for m in [".get(", ".post(", ".put(", ".delete(", ".patch("]):
                        is_route = True
                        route_method = dec_str
                        break

                doc = ast.get_docstring(node)
                sig = f"async def {node.name}(...)" if stype == "async_function" else f"def {node.name}(...)"
                if is_route:
                    sig = f"{route_method} -> {sig}"
                    stype = "route"

                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        symbol_type=stype,
                        file_path=rel_path,
                        line_number=node.lineno,
                        signature=sig,
                        docstring=doc,
                    )
                )
        return symbols

    def _extract_ts_symbols(self, file_path: Path, rel_path: str) -> List[CodeSymbol]:
        """Extracts symbols from TypeScript and TSX files using regex heuristics."""
        symbols: List[CodeSymbol] = []
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except Exception:
            return symbols

        interface_pattern = re.compile(r"^\s*export\s+interface\s+([A-Za-z0-9_]+)")
        type_pattern = re.compile(r"^\s*export\s+type\s+([A-Za-z0-9_]+)")
        func_pattern = re.compile(r"^\s*export\s+(?:async\s+)?function\s+([A-Za-z0-9_]+)")
        react_comp_pattern = re.compile(r"^\s*export\s+const\s+([A-Za-z0-9_]+)\s*:\s*React\.FC")

        for idx, line in enumerate(lines, start=1):
            if m := react_comp_pattern.search(line):
                symbols.append(
                    CodeSymbol(
                        name=m.group(1),
                        symbol_type="react_component",
                        file_path=rel_path,
                        line_number=idx,
                        signature=line.strip(),
                    )
                )
            elif m := interface_pattern.search(line):
                symbols.append(
                    CodeSymbol(
                        name=m.group(1),
                        symbol_type="interface",
                        file_path=rel_path,
                        line_number=idx,
                        signature=line.strip(),
                    )
                )
            elif m := type_pattern.search(line):
                symbols.append(
                    CodeSymbol(
                        name=m.group(1),
                        symbol_type="type_alias",
                        file_path=rel_path,
                        line_number=idx,
                        signature=line.strip(),
                    )
                )
            elif m := func_pattern.search(line):
                symbols.append(
                    CodeSymbol(
                        name=m.group(1),
                        symbol_type="function",
                        file_path=rel_path,
                        line_number=idx,
                        signature=line.strip(),
                    )
                )
        return symbols

    def search_symbols(
        self, query: str, symbol_type: Optional[str] = None, max_results: int = 30
    ) -> List[Dict[str, Any]]:
        """Scans codebase for classes, functions, routes, and interfaces matching query."""
        clean_q = query.lower().strip()
        matched: List[Dict[str, Any]] = []

        scan_dirs = [self.sandbox_root / "backend", self.sandbox_root / "frontend"]

        for scan_dir in scan_dirs:
            if not scan_dir.exists():
                continue
            for root, dirs, files in os.walk(scan_dir):
                dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")]
                for f in files:
                    p = Path(root) / f
                    ext = p.suffix.lower()
                    if ext in IGNORED_EXTENSIONS:
                        continue

                    try:
                        rel = str(p.relative_to(self.sandbox_root))
                    except Exception:
                        rel = p.name

                    file_symbols: List[CodeSymbol] = []
                    if ext == ".py":
                        file_symbols = self._extract_python_symbols(p, rel)
                    elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                        file_symbols = self._extract_ts_symbols(p, rel)

                    for sym in file_symbols:
                        if symbol_type and sym.symbol_type.lower() != symbol_type.lower():
                            continue
                        if clean_q in sym.name.lower() or (sym.docstring and clean_q in sym.docstring.lower()):
                            matched.append({
                                "name": sym.name,
                                "type": sym.symbol_type,
                                "file": sym.file_path,
                                "line": sym.line_number,
                                "signature": sym.signature,
                                "docstring": sym.docstring,
                            })
                            if len(matched) >= max_results:
                                return matched

        return matched

    def inspect_file(self, relative_path: str) -> Dict[str, Any]:
        """Provides a detailed structural summary of a specific code file."""
        target = (self.sandbox_root / relative_path).resolve()
        if not self.is_safe_path(str(target)) or not target.is_file():
            return {
                "error": f"File '{relative_path}' is outside sandbox or does not exist, {self.form_of_address}.",
                "metrics": None,
            }

        try:
            content = target.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            line_count = len(lines)
            size_bytes = target.stat().st_size
            ext = target.suffix.lower()

            symbols = []
            if ext == ".py":
                symbols = self._extract_python_symbols(target, relative_path)
            elif ext in [".ts", ".tsx"]:
                symbols = self._extract_ts_symbols(target, relative_path)

            return {
                "file": relative_path,
                "lines": line_count,
                "size_bytes": size_bytes,
                "symbol_count": len(symbols),
                "symbols": [
                    {"name": s.name, "type": s.symbol_type, "line": s.line_number, "signature": s.signature}
                    for s in symbols[:20]
                ],
                "summary": (
                    f"File '{relative_path}' contains {line_count} lines and {len(symbols)} primary symbols, "
                    f"{self.form_of_address}."
                ),
            }
        except Exception as e:
            return {"error": str(e), "file": relative_path}

    def get_codebase_overview(self) -> Dict[str, Any]:
        """Calculates global codebase statistics across sandbox."""
        stats = {
            "python_files": 0,
            "ts_files": 0,
            "markdown_files": 0,
            "other_files": 0,
            "total_lines": 0,
            "python_lines": 0,
            "ts_lines": 0,
        }

        for root, dirs, files in os.walk(self.sandbox_root):
            dirs[:] = [d for d in dirs if d not in IGNORED_DIRECTORIES and not d.startswith(".")]
            for f in files:
                p = Path(root) / f
                ext = p.suffix.lower()
                if ext in IGNORED_EXTENSIONS:
                    continue

                try:
                    with p.open("rb") as f:
                        line_count = sum(1 for _ in f)
                    stats["total_lines"] += line_count
                    if ext == ".py":
                        stats["python_files"] += 1
                        stats["python_lines"] += line_count
                    elif ext in [".ts", ".tsx"]:
                        stats["ts_files"] += 1
                        stats["ts_lines"] += line_count
                    elif ext in [".md", ".markdown"]:
                        stats["markdown_files"] += 1
                    else:
                        stats["other_files"] += 1
                except Exception:
                    pass

        summary = (
            f"Here is your project codebase overview, {self.form_of_address}:\n\n"
            f"• **Python Engine**: {stats['python_files']} modules ({stats['python_lines']} lines of code).\n"
            f"• **TypeScript Frontend**: {stats['ts_files']} source files ({stats['ts_lines']} lines of code).\n"
            f"• **Documentation**: {stats['markdown_files']} technical architecture documents.\n"
            f"• **Total Tracked Code**: {stats['total_lines']} total lines.\n\n"
            f"The entire codebase is structured cleanly and ready for inspection, {self.form_of_address}."
        )

        return {"stats": stats, "summary": summary}


codebase_inspector = CodebaseInspector()
