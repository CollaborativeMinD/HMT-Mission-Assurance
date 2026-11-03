"""Classify and hash published artifacts without copying private source material."""

import argparse
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from hmt_mission_assurance import __version__
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


def inventory(baseline_files: set[str], changed: set[str], timestamp: str) -> list[dict]:
    records = []
    for path in release_files():
        relative = str(path.relative_to(ROOT))
        if relative in META:
            continue
        import hashlib

        records.append(
            {
                "path": relative,
                "classification": "new"
                if relative not in baseline_files
                else "modified"
                if relative in changed
                else "inherited",
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "size_bytes": path.stat().st_size,
                "recorded_at": timestamp,
                "source": "Apache-2.0 standard text"
                if relative == "LICENSE"
                else "public-reference-implementation",
            }
        )
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", required=True, help="Reviewed prior release commit")
    args = parser.parse_args()
    baseline_files = set(
        subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", args.baseline], cwd=ROOT, text=True
        ).splitlines()
    )
    changed = set(
        subprocess.check_output(
            ["git", "diff", "--name-only", args.baseline], cwd=ROOT, text=True
        ).splitlines()
    )
    timestamp = datetime.now(UTC).isoformat()
    records = inventory(baseline_files, changed, timestamp)
    provenance = ROOT / "evidence/provenance.jsonl"
    provenance.write_text("\n".join(json.dumps(r, sort_keys=True) for r in records) + "\n")
    records.append(
        {
            "path": "evidence/provenance.jsonl",
            "classification": "modified",
            "sha256": sha256(provenance.read_text()),
            "size_bytes": provenance.stat().st_size,
            "recorded_at": timestamp,
            "source": "release_manifest.py",
        }
    )
    manifest = {
        "version": __version__,
        "baseline_commit": args.baseline,
        "recorded_at": timestamp,
        "artifacts": records,
        "modified": [r["path"] for r in records if r["classification"] == "modified"],
        "blocked": ["Signed-in host-client acceptance is unverified; see evidence/connections.json"],
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
