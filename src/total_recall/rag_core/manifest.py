from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class FileFingerprint:
    path: str
    sha256: str


class VaultManifest:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, str]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def save(self, fingerprints: dict[str, str]) -> None:
        self.path.write_text(json.dumps(fingerprints, indent=2, sort_keys=True), encoding="utf-8")


def fingerprint_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compute_vault_fingerprints(vault_path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for md in sorted(vault_path.rglob("*.md")):
        values[str(md)] = fingerprint_file(md)
    return values
