"""Deterministic clinical-trial analysis engine for ATLAS.

The engine is intentionally dependency-free so it can run in a hackathon
environment with only Python 3.10+.
"""
from __future__ import annotations

import csv
import io
import math
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class Evidence:
    domain: str
    record_ref: str
    reason: str

    def as_dict(self) -> dict[str, str]:
        return {"domain": self.domain, "record_ref": self.record_ref, "reason": self.reason}


class AtlasEngine:
    def __init__(self, tables: dict[str, list[dict[str, str]]] | None = None):
        self.tables = tables or {}
        self.reference_ranges = self._index_ranges(self.tables.get("reference_ranges", []))

    @staticmethod
    def _index_ranges(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], tuple[float, float]]:
        result = {}
        for row in rows:
            try:
                result[(row.get("LBTESTCD", ""), row.get("UNIT", ""), row.get("LAB", ""))] = (float(row["LOW"]), float(row["HIGH"]))
            except (KeyError, ValueError):
                continue
        return result

    @staticmethod
    def from_csv_texts(files: dict[str, str]) -> "AtlasEngine":
        tables = {}
        for name, text in files.items():
            reader = csv.DictReader(io.StringIO(text))
            tables[name.rsplit(".", 1)[0].upper()] = list(reader)
        return AtlasEngine(tables)

    @staticmethod
    def _num(value: str) -> float | None:
        if value is None or not str(value).strip() or str(value).strip().upper() in {"ND", "NA", "N/A"}:
            return None
        match = re.fullmatch(r"\s*<?\s*(-?\d+(?:\.\d+)?)\s*", str(value))
        return float(match.group(1)) if match else None

    @staticmethod
    def _date(value: str) -> datetime | None:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value[:19], fmt)
            except ValueError:
                pass
        return None

    def summary(self) -> dict[str, Any]:
        dm = self.tables.get("DM", [])
        sites = {r.get("SITEID") for r in dm if r.get("SITEID")}
        return {
            "subjects": len({r.get("USUBJID") for r in dm if r.get("USUBJID")}),
            "sites": len(sites),
            "domains": {k: len(v) for k, v in self.tables.items()},
            "safety_signals": len(self.safety_signals()),
        }

    def safety_signals(self) -> list[dict[str, Any]]:
        signals = []
        excluded_sites = {"S03", "S07"}
        dm_sites = {r.get("USUBJID"): r.get("SITEID") for r in self.tables.get("DM", [])}
        for index, row in enumerate(self.tables.get("LB", []), start=1):
            subject = row.get("USUBJID", "")
            site = dm_sites.get(subject, "")
            if site in excluded_sites:
                continue
            raw = row.get("LBORRES", "")
            value = self._num(raw)
            if value is None:
                continue
            test = row.get("LBTESTCD", "")
            unit = row.get("LBORRESU", "")
            lab = site if site == "S07" else "CENTRAL"
            converted = value
            normalized_unit = unit
            if site == "S07" and test in {"ALT", "AST"} and unit in {"ukat/L", "µkat/L"}:
                converted = value * 60
                normalized_unit = "U/L"
                lab = "CENTRAL"
            bounds = self.reference_ranges.get((test, normalized_unit, lab))
            if not bounds and site == "S07":
                bounds = self.reference_ranges.get((test, unit, "S07"))
            if bounds and (converted < bounds[0] or converted > bounds[1]):
                signals.append({
                    "type": "laboratory_out_of_range",
                    "subject": subject,
                    "site": site,
                    "test": test,
                    "value": converted,
                    "unit": normalized_unit,
                    "reference": {"low": bounds[0], "high": bounds[1]},
                    "evidence": [Evidence("LB", f"LB:{subject}:{row.get('LBSEQ', index)}", "Value outside applicable reference range").as_dict()],
                })
        return signals

    def query(self, question: str) -> dict[str, Any]:
        q = question.lower().strip()
        if any(word in q for word in ("how many subjects", "subject count", "enrolled")):
            count = self.summary()["subjects"]
            return {"answer": f"{count} unique subjects are present in the DM dataset.", "confidence": "high", "evidence": [Evidence("DM", "DM:USUBJID", "Unique subject identifiers counted").as_dict()]}
        if "site" in q and ("how many" in q or "count" in q):
            count = self.summary()["sites"]
            return {"answer": f"{count} distinct sites are present in the DM dataset.", "confidence": "high", "evidence": [Evidence("DM", "DM:SITEID", "Distinct site identifiers counted").as_dict()]}
        if any(word in q for word in ("safety", "lab", "laboratory", "out of range")):
            signals = self.safety_signals()
            return {"answer": f"{len(signals)} potential laboratory out-of-range records were detected after applying the exclusion and conversion rules.", "confidence": "medium", "evidence": [Evidence("LB", "LB:derived-signal-set", "Deterministic reference-range evaluation").as_dict()], "findings": signals[:100]}
        return {"answer": "The question was received, but no deterministic rule currently matches it.", "confidence": "low", "evidence": [], "needs_review": True}
