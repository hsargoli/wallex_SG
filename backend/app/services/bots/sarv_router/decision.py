"""DecisionReason — Copilot decision contract (ADR-0040)."""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class DecisionReason:
    """Copilot decision output with backward-compatible dict form.

    Per ADR-0040 §2.1: evidence keys are spread to top level (old consumers
    keep working); Copilot keys are layered on top.
    """
    action: str
    why: str
    evidence: dict
    confidence: float
    tick_id: str
    risk: dict | None = None
    alternatives: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Return old-shape dict + Copilot keys (ADR-0040 §2.2)."""
        out = dict(self.evidence)  # preserve path-specific old keys
        out["action"] = self.action  # self.action is source of truth
        out["why"] = self.why
        out["evidence"] = self.evidence
        out["confidence"] = self.confidence
        out["tick_id"] = self.tick_id
        if self.risk is not None:
            out["risk"] = self.risk
        if self.alternatives:
            out["alternatives"] = list(self.alternatives)
        return out
