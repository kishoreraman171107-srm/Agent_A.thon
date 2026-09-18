"""Generic data-quality checks for unseen Study Sentinel datasets."""
from __future__ import annotations

from typing import Any


def validate_tables(tables: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    """Return structural diagnostics without relying on study-specific IDs."""
    diagnostics: list[dict[str, Any]] = []
    for domain, rows in tables.items():
        if not rows:
            diagnostics.append({"domain": domain, "issue": "empty_domain", "count": 0})
            continue
        for index, row in enumerate(rows, start=1):
            subject = row.get("USUBJID", "")
            seq_key = f"{domain}SEQ"
            if not subject:
                diagnostics.append({"domain": domain, "row": index, "issue": "missing_USUBJID"})
            if not row.get(seq_key):
                diagnostics.append({"domain": domain, "row": index, "issue": f"missing_{seq_key}"})
    return {"valid": not diagnostics, "issues": diagnostics, "issue_count": len(diagnostics)}


def evidence_ref(domain: str, row: dict[str, str], fallback_seq: int) -> str:
    """Build the required domain|subject|sequence evidence identifier."""
    subject = row.get("USUBJID", "")
    sequence = row.get(f"{domain}SEQ") or str(fallback_seq)
    return f"{domain}|{subject}|{sequence}"
