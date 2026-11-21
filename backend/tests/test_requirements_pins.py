"""Git-pinned dependencies must name an immutable ref (yoga_sutras #10).

Mirrors ramayanam ``tests/unit/test_requirements_pins.py``. ``sanskrit-analyzer``
must be pinned to a full commit SHA: a moving ref such as ``@main`` is treated
by pip as already satisfied, so a cached build keeps a stale analyzer.
"""
import re
from pathlib import Path

import pytest

REQUIREMENTS = Path(__file__).resolve().parents[1] / "requirements.txt"
_PIN_RE = re.compile(r"^(?P<pkg>[A-Za-z0-9._-]+)(\[[^\]]*\])?\s*@\s*git\+[^@\s]+@(?P<ref>[^#\s]+)")
_FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
_MOVING_REFS = {"main", "master", "HEAD", "develop"}


def _git_pins() -> dict[str, str]:
    pins = {}
    for raw in REQUIREMENTS.read_text(encoding="utf-8").splitlines():
        match = _PIN_RE.match(raw.strip())
        if match:
            pins[match.group("pkg")] = match.group("ref")
    return pins


@pytest.mark.parametrize(
    "pkg, rule",
    [
        ("sanskrit-analyzer", "full_sha"),
        ("homelab-observability", "not_moving"),
    ],
)
def test_git_pin_is_immutable(pkg, rule):
    pins = _git_pins()
    assert pkg in pins, f"{pkg} is no longer a git dependency in {REQUIREMENTS.name}"
    ref = pins[pkg]
    assert ref not in _MOVING_REFS, f"{pkg} pinned to moving ref @{ref}"
    if rule == "full_sha":
        assert _FULL_SHA_RE.match(ref), f"{pkg} must pin a 40-char commit SHA, got @{ref}"
