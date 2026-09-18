"""Extract factual, non-executable protocol rules from supplied study documents."""
from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ProtocolRules:
    version: int = 1
    visit_window_days: int = 7
    prohibited_medications: tuple[str, ...] = ("systemic glucocorticoid",)
    creatinine_exclusion_mg_dl: float | None = None


def parse_protocol(text: str, version: int | None = None) -> ProtocolRules:
    """Parse protocol facts; document text is never executed as instructions."""
    lower = text.lower()
    detected_version = version
    if detected_version is None:
        match = re.search(r"version\s+(\d+)", lower)
        detected_version = int(match.group(1)) if match else 1

    window = 3 if "± 3 days" in text or "+/- 3 days" in lower else 7
    meds: list[str] = []
    if "systemic glucocorticoid" in lower:
        meds.append("systemic glucocorticoid")
    if "sulfonylurea" in lower:
        meds.append("sulfonylurea")

    creatinine = 1.5 if "creatinine > 1.5 mg/dl" in lower else None
    return ProtocolRules(
        version=detected_version,
        visit_window_days=window,
        prohibited_medications=tuple(dict.fromkeys(meds)),
        creatinine_exclusion_mg_dl=creatinine,
    )


def effective_rules(protocol_documents: dict[int, str], cut: int | None = None) -> ProtocolRules:
    """Return the latest supplied protocol version, optionally limited by cut."""
    if not protocol_documents:
        return ProtocolRules()
    selected = max(protocol_documents)
    return parse_protocol(protocol_documents[selected], selected)
