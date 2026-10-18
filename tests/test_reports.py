import json
from pathlib import Path

from hmt_mission_assurance.contract import EvaluationContract
from hmt_mission_assurance.encoding import canonical
from hmt_mission_assurance.reports import cell, emit_delta_report


def test_graph_fidelity_and_machine_record():
    root = Path(__file__).resolve().parents[1]
    contract = EvaluationContract.model_validate_json((root / "examples/coupled.json").read_text())
    bundle = emit_delta_report(contract)
    graph = bundle.evaluation.graph
    ids = {n.id for n in graph.nodes}
    assert len(ids) == len(graph.nodes)
    assert all(edge.source in ids and edge.target in ids for edge in graph.edges)
    assert sum(n.kind == "coupling" for n in graph.nodes) == len(contract.couplings)
    assert sum(n.kind == "scenario" for n in graph.nodes) == 6
    assert len(graph.nodes) == 16
    assert "```mermaid" in bundle.markdown and "## Traceability matrix" in bundle.markdown
    record = bundle.markdown.split("```json\n")[1].split("\n```")[0]
    assert json.loads(record) == bundle.evaluation.model_dump(mode="json")
    assert bundle == emit_delta_report(contract)


def test_html_and_markdown_injection(raw):
    attack = '</script><img src=x onerror=alert(1)>|`\n```mermaid\nclick X "https://evil"'
    raw["scope"] = attack
    raw["evidence"][0]["source_ref"] = attack
    contract = EvaluationContract.model_validate_json(canonical(raw))
    bundle = emit_delta_report(contract)
    assert attack not in bundle.html
    assert "\\u003c/script\\u003e" in bundle.html
    assert "connect-src &#x27;none&#x27;" not in bundle.html
    assert "connect-src 'none'" in bundle.html
    assert "<img src=x" not in bundle.markdown
    assert "\\|" in cell(attack) and "\\`" in cell(attack)
    assert bundle.markdown.count("```mermaid") == 1


def test_full_findings_and_requirements_visible(raw):
    raw["evidence"] = []
    bundle = emit_delta_report(EvaluationContract.model_validate_json(canonical(raw)))
    for item in bundle.evaluation.findings + bundle.evaluation.requirements:
        assert item.id in bundle.markdown and item.id in bundle.html
    assert all(f"{n.id}" in bundle.html for n in bundle.evaluation.graph.nodes)


def test_text_escaping():
    assert "\\[" in cell("[link]")
    assert "&lt;" in cell("<")
