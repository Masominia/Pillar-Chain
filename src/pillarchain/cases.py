"""The library of networks: discovery and description."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def discover(directory: Path) -> list[Path]:
    return sorted(directory.glob("*.pil"))


def notes(path: Path) -> list[str]:
    """The comment lines at the top of a case: what it shows and what it is checked against."""
    out = []
    for line in path.read_text().splitlines():
        if not line.startswith("#"):
            break
        out.append(line[1:].strip())
    return out


def family_of(name: str, families: dict[str, list[str]]) -> str:
    for family, prefixes in families.items():
        if any(name.startswith(p) for p in prefixes):
            return family
    return "other"


def write_record(record: dict, directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{record['case']}.json"
    path.write_text(json.dumps(record, indent=1) + "\n")
    return path
