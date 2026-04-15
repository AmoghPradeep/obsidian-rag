from pathlib import Path

from total_recall.rag_core.manifest import VaultManifest, compute_vault_fingerprints


def test_manifest_detects_changes(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    md = vault / "a.md"
    md.write_text("hello", encoding="utf-8")

    manifest = VaultManifest(tmp_path / "manifest.json")
    f1 = compute_vault_fingerprints(vault)
    manifest.save(f1)
    loaded = manifest.load()
    assert loaded == f1

    md.write_text("hello changed", encoding="utf-8")
    f2 = compute_vault_fingerprints(vault)
    assert f2[str(md)] != f1[str(md)]
