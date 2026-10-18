"""A complete declared graph, without inventing or enumerating transitive paths."""

from .contract import EvaluationContract
from .results import Edge, EvaluationResult, Graph, Node


def build_graph(contract: EvaluationContract, result: EvaluationResult) -> Graph:
    nodes: list[Node] = []
    edges: list[Edge] = []
    for claim in contract.claims:
        nodes.append(Node(id="claim:" + claim.id, kind="claim", label=claim.statement))
        for scenario in claim.scenarios:
            nodes.append(Node(id="scenario:" + scenario.id, kind="scenario", label=scenario.description))
            edges.append(
                Edge(source="claim:" + claim.id, target="scenario:" + scenario.id, relation=scenario.mode)
            )
    for evidence in contract.evidence:
        nodes.append(Node(id="evidence:" + evidence.id, kind="evidence", label=evidence.source_ref))
        edges.append(
            Edge(
                source="scenario:" + evidence.scenario_id,
                target="evidence:" + evidence.id,
                relation="submitted",
            )
        )
    for item in result.findings:
        nodes.append(Node(id="finding:" + item.id, kind="finding", label=item.reason_code))
        anchor = "scenario:" + item.scenario_id if item.scenario_id else "claim:" + item.claim_id
        edges.append(Edge(source=anchor, target="finding:" + item.id, relation="finding"))
        for ref in item.evidence_refs:
            edges.append(Edge(source="evidence:" + ref, target="finding:" + item.id, relation="basis"))
    for requirement in result.requirements:
        nodes.append(
            Node(
                id="requirement:" + requirement.id, kind="requirement", label=requirement.acceptance_threshold
            )
        )
        edges.append(
            Edge(
                source="finding:" + requirement.finding_id,
                target="requirement:" + requirement.id,
                relation="derive",
            )
        )
    coupling_graph(contract, nodes, edges)
    nodes.append(Node(id="disposition:primary", kind="disposition", label=result.primary_disposition))
    for item in result.findings:
        edges.append(
            Edge(source="finding:" + item.id, target="disposition:primary", relation=item.disposition)
        )
    if not result.findings:
        for claim in contract.claims:
            edges.append(
                Edge(source="claim:" + claim.id, target="disposition:primary", relation="scoped_match")
            )
    return Graph(
        nodes=tuple(sorted(nodes, key=lambda n: n.id)),
        edges=tuple(sorted(edges, key=lambda e: (e.source, e.target, e.relation))),
    )


def coupling_graph(contract: EvaluationContract, nodes: list[Node], edges: list[Edge]) -> None:
    for coupling in contract.couplings:
        nodes.append(Node(id="coupling:" + coupling.id, kind="coupling", label=coupling.description))
        edges.extend(
            (
                Edge(
                    source="claim:" + coupling.source_claim,
                    target="coupling:" + coupling.id,
                    relation="depends",
                ),
                Edge(
                    source="coupling:" + coupling.id,
                    target="claim:" + coupling.target_claim,
                    relation="receives",
                ),
                Edge(
                    source="coupling:" + coupling.id,
                    target="scenario:" + coupling.scenario_id,
                    relation="witness",
                ),
            )
        )
