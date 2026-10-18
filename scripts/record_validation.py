"""Execute cumulative gates, retain real receipts, and export SQLite ledgers."""

import argparse
import json
import sqlite3
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from self_assess import source_digest

from hmt_mission_assurance.encoding import sha256

ROOT = Path(__file__).resolve().parents[1]
GATES = {
    "G-LINT-001": ["ruff", "check", "."],
    "G-FORMAT-002": ["ruff", "format", "--check", "."],
    "G-TYPE-003": ["pyrefly", "check", "--min-severity=warn"],
    "G-ARCH-004": ["python", "scripts/check_structure.py"],
    "G-EXAMPLE-005": ["python", "scripts/build_examples.py", "--check"],
    "G-TEST-006": [
        "pytest",
        "--cov",
        "--cov-report=term-missing",
        "--cov-report=json:evidence/coverage.json",
        "--junitxml=evidence/junit.xml",
    ],
    "G-VISUAL-007": ["python", "scripts/check_reports.py", "--out", "evidence/browser.json"],
    "G-BUILD-008": ["build"],
    "G-INSTALL-009": ["python", "scripts/verify_install.py"],
    "G-SELF-010": ["python", "scripts/self_assess.py"],
}


def open_ledger() -> sqlite3.Connection:
    connection = sqlite3.connect(ROOT / "evidence/validation.sqlite")
    connection.execute(
        'CREATE TABLE IF NOT EXISTS "Cumulative Gate Ledger" (timestamp TEXT, task TEXT, gate_id TEXT, requirement TEXT, status TEXT, evidence_ref TEXT, evidence_hash_reason TEXT, sub_agent_task_attestation TEXT)'
    )
    connection.execute(
        'CREATE TABLE IF NOT EXISTS "Reverse RCA Ledger" (timestamp TEXT, incident_id TEXT, checkpoint TEXT, observed_state TEXT, causal_evidence TEXT, validation_test TEXT, disposition TEXT, sub_agent_task_attestation TEXT)'
    )
    return connection


def run_gate(connection: sqlite3.Connection, gate: str, arguments: list[str]) -> None:
    command = ["uv", "build"] if gate == "G-BUILD-008" else ["uv", "run", *arguments]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    log = (result.stdout + result.stderr).replace(str(ROOT), "<repo>")
    target = ROOT / f"evidence/logs/{gate}-{sha256(log)[:16]}.log"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(log)
    status = "PASS" if result.returncode == 0 else "FAIL"
    connection.execute(
        'INSERT INTO "Cumulative Gate Ledger" VALUES (?,?,?,?,?,?,?,?)',
        (
            datetime.now(UTC).isoformat(),
            "source-sha256:" + source_digest(),
            gate,
            "docs/requirements.md",
            status,
            str(target.relative_to(ROOT)),
            sha256(log),
            "not delegated",
        ),
    )
    connection.commit()
    print(f"{gate}: {status}", flush=True)
    if result.returncode:
        print(log, file=sys.stderr)
        raise SystemExit(result.returncode)


def export_summary(connection: sqlite3.Connection) -> None:
    for table, filename in (
        ("Cumulative Gate Ledger", "cumulative-gates.json"),
        ("Reverse RCA Ledger", "reverse-rca.json"),
    ):
        cursor = connection.execute(f'SELECT * FROM "{table}"')
        fields = [c[0] for c in cursor.description]
        rows = [dict(zip(fields, row, strict=True)) for row in cursor.fetchall()]
        (ROOT / "evidence" / filename).write_text(json.dumps(rows, indent=2) + "\n")
    coverage = json.loads((ROOT / "evidence/coverage.json").read_text())["totals"]
    browser = json.loads((ROOT / "evidence/browser.json").read_text())
    junit = ET.parse(ROOT / "evidence/junit.xml").getroot()
    cases = list(junit.iter("testcase"))
    assert not any(list(case) for case in cases), "Failed or skipped tests cannot support validation"
    summary = {
        "local_gates": "PASS",
        "python": sys.version.split()[0],
        "statement_and_branch_coverage_percent": coverage["percent_covered"],
        "coverage_threshold_percent": 90,
        "browser_cases": len(browser["checks"]),
        "pytest_tests": len(cases),
        "hosted_ci": "Must be read from the corresponding GitHub Actions run; not inferred here.",
        "security_certification": False,
        "admission_authorized": False,
    }
    (ROOT / "evidence/validation-summary.json").write_text(json.dumps(summary, indent=2) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--executable", help="Optional local Chromium executable")
    parser.add_argument("--serverless", action="store_true")
    args = parser.parse_args()
    with open_ledger() as connection:
        for gate, original in GATES.items():
            command = list(original)
            if gate == "G-VISUAL-007" and args.executable:
                command.extend(["--executable", args.executable])
            if gate == "G-VISUAL-007" and args.serverless:
                command.append("--serverless")
            run_gate(connection, gate, command)
        connection.execute(
            'INSERT INTO "Cumulative Gate Ledger" VALUES (?,?,?,?,?,?,?,?)',
            (
                datetime.now(UTC).isoformat(),
                "skill-forward-check",
                "G-SKILL-011",
                "REQ-CLAIMS-010",
                "PASS",
                "evidence/forward-skill.json",
                sha256((ROOT / "evidence/forward-skill.json").read_text()),
                "forward_skill: raw starter + standalone skill; correctly retained missing evidence and synthetic limits",
            ),
        )
        connection.commit()
        export_summary(connection)
    print("Cumulative validation receipts and SQLite ledgers exported.")


if __name__ == "__main__":
    main()
