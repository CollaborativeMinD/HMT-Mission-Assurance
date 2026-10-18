"""Classify and hash published artifacts without copying private source material."""

import json
from datetime import UTC, datetime
from pathlib import Path

from hmt_mission_assurance.encoding import sha256

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED = {".git", ".venv", ".pytest_cache", ".ruff_cache", "__pycache__", "dist"}
META = {"evidence/artifact-manifest.json", "evidence/provenance.jsonl"}


def release_files() -> list[Path]:
    return sorted(
        p
        for p in ROOT.rglob("*")
        if p.is_file()
        and not (set(p.relative_to(ROOT).parts) & EXCLUDED)
        and p.name != ".coverage"
        and not p.name.endswith(".egg-info")
    )


def main() -> None:
    timestamp = datetime.now(UTC).isoformat()
    records = []
    for path in release_files():
        relative = str(path.relative_to(ROOT))
        if relative in META:
            continue
        import hashlib

        records.append(
            {
                "path": relative,
                "classification": "inherited" if relative == "LICENSE" else "new",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
                "recorded_at": timestamp,
                "source": "Apache-2.0 standard text"
                if relative == "LICENSE"
                else "public-reference-implementation",
            }
        )
    provenance = ROOT / "evidence/provenance.jsonl"
    provenance.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n")
    records.append(
        {
            "path": "evidence/provenance.jsonl",
            "classification": "new",
            "sha256": sha256(provenance.read_text()),
            "size_bytes": provenance.stat().st_size,
            "recorded_at": timestamp,
            "source": "release_manifest.py",
        }
    )
    manifest = {
        "version": "0.1.0",
        "recorded_at": timestamp,
        "artifacts": records,
        "modified": [],
        "blocked": [],
        "excluded": [
            "Internal uploads, kernels, policy corpus, and exploration are outside this repository.",
            "Build distributions and transient runtime/cache files are excluded from the source tree.",
            "This manifest cannot hash itself; its exact bytes are bound by the Git commit tree.",
        ],
        "provenance_limit": "Inventory records source/classification at release assembly; not proof of authorship or execution.",
    }
    (ROOT / "evidence/artifact-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    verify(manifest)
    print(f"G-MANIFEST-012: PASS ({len(records)} classified artifacts; manifest bound by Git)")


def verify(manifest: dict) -> None:
    import hashlib

    for item in manifest["artifacts"]:
        path = ROOT / item["path"]
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"], item["path"]
    expected = {r["path"] for r in manifest["artifacts"]} | {"evidence/artifact-manifest.json"}
    assert {str(p.relative_to(ROOT)) for p in release_files()} == expected


if __name__ == "__main__":
    main()
