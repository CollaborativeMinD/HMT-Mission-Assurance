"""The public evaluation contract. All submitted material is untrusted data."""

from datetime import datetime
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

Identifier = Annotated[str, StringConstraints(pattern=r"^[A-Za-z][A-Za-z0-9_-]{0,63}$")]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Digest = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]
Mode = Literal["positive", "negative", "regression"]
Disposition = Literal[
    "STABLE_AS_IS", "UPDATE_REQUIRED", "SEMANTIC_DRIFT_DETECTED", "HOLD", "INSUFFICIENT_EVIDENCE"
]


class Model(BaseModel):
    model_config = ConfigDict(
        strict=True, frozen=True, extra="forbid", validate_default=True, allow_inf_nan=False
    )


def utc_time(value: str) -> datetime:
    """Accept explicit UTC instants; do not consult the host clock."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    offset = parsed.utcoffset()
    if offset is None or offset.total_seconds() != 0:
        raise ValueError("timestamp must have an explicit UTC offset")
    return parsed


class Scenario(Model):
    id: Identifier
    description: Text
    mode: Mode
    expected: Text
    blocking: bool = False
    semantic: bool = False


class Claim(Model):
    id: Identifier
    statement: Text
    code_refs: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]
    scenarios: Annotated[tuple[Scenario, ...], Field(min_length=1, max_length=16)]


class Witness(Model):
    """A producer assertion about an executed case, not an authenticated attestation."""

    scenario_id: Identifier
    actual: Text
    case_id: Text
    run_id: Identifier
    producer: Text
    method: Literal["executed", "narrative"]


class Evidence(Model):
    id: Identifier
    scenario_id: Identifier
    source_ref: Text
    tool_id: Identifier
    baseline_version: Text
    environment_id: Identifier
    captured_at: Annotated[str, Field(max_length=40)]
    content: Annotated[str, Field(min_length=1, max_length=16000)]
    sha256: Digest

    @field_validator("captured_at")
    @classmethod
    def validate_time(cls, value: str) -> str:
        utc_time(value)
        return value


class Coupling(Model):
    """A declared dependency; its witness must exercise the receiving claim."""

    id: Identifier
    source_claim: Identifier
    target_claim: Identifier
    scenario_id: Identifier
    description: Text


class EvaluationContract(Model):
    schema_version: Literal["1.0"] = "1.0"
    tool_id: Identifier
    baseline_version: Text
    scope: Text
    limitations: Annotated[tuple[Text, ...], Field(min_length=1, max_length=16)]
    as_of: Annotated[str, Field(max_length=40)]
    environment_id: Identifier
    max_age_seconds: Annotated[int, Field(ge=1, le=31536000)] = 86400
    claims: Annotated[tuple[Claim, ...], Field(min_length=1, max_length=32)]
    evidence: Annotated[tuple[Evidence, ...], Field(max_length=256)] = ()
    couplings: Annotated[tuple[Coupling, ...], Field(max_length=64)] = ()

    @field_validator("as_of")
    @classmethod
    def validate_time(cls, value: str) -> str:
        utc_time(value)
        return value

    @model_validator(mode="after")
    def validate_links(self) -> Self:
        scenario_owner = {s.id: c.id for c in self.claims for s in c.scenarios}
        scenarios = [s.id for c in self.claims for s in c.scenarios]
        identifiers = [c.id for c in self.claims] + scenarios
        identifiers += [e.id for e in self.evidence] + [c.id for c in self.couplings]
        if len(identifiers) != len(set(identifiers)):
            raise ValueError("all graph identifiers must be globally unique")
        if len(scenarios) > 128:
            raise ValueError("at most 128 scenarios per evaluation")
        claim_ids = {c.id for c in self.claims}
        for evidence in self.evidence:
            if evidence.scenario_id not in scenario_owner:
                raise ValueError("evidence has an unresolved scenario reference")
        for coupling in self.couplings:
            if {coupling.source_claim, coupling.target_claim} - claim_ids:
                raise ValueError("coupling has an unresolved claim reference")
            if coupling.source_claim == coupling.target_claim:
                raise ValueError("self-couplings are not supported")
            if scenario_owner.get(coupling.scenario_id) != coupling.target_claim:
                raise ValueError("coupling scenario must belong to its target claim")
        return self


class ToolRequest(Model):
    contract: EvaluationContract
