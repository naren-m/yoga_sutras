"""Sanskrit NLP boundary (yoga_sutras #10, ramayanam #509 W7).

``sanskrit_analyzer`` is the only source of Sanskrit knowledge. App code
imports it, never the low-level engines underneath it.
"""
import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCANNED = ("backend/app", "backend/run.py", "scripts")
BANNED = ("indic_transliteration", "vidyut", "dharmamitra", "sanskrit_parser")

# Known violations. Shrink this, never grow it.
ALLOWED: set = set()


def _py_files():
    for rel in SCANNED:
        path = REPO_ROOT / rel
        yield from ([path] if path.is_file() else sorted(path.rglob("*.py")))


def _banned_imports(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        else:
            continue
        for name in names:
            top = name.split(".")[0]
            if top in BANNED:
                yield top, node.lineno


def _violations():
    found = set()
    for path in _py_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        for top, _ in _banned_imports(path):
            found.add((rel, top))
    return found


@pytest.mark.parametrize(
    "check",
    ["no_new_violations", "allowlist_not_stale"],
)
def test_sanskrit_boundary(check):
    found = _violations()
    if check == "no_new_violations":
        new = sorted(found - ALLOWED)
        assert not new, f"import sanskrit_analyzer instead of: {new}"
    else:
        stale = sorted(ALLOWED - found)
        assert not stale, f"fixed; remove from ALLOWED: {stale}"
