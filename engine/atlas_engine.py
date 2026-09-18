"""Deterministic, evidence-traceable clinical-trial analysis engine."""
from __future__ import annotations

import csv
import io
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
    EXCLUDED_SITES = {"S03", "S07"}
    UNIT_CONVERSIONS = {"µkat/L": 60.0, "ukat/L": 60.0}

    def __init__(self, tables: dict[str, list[dict[str, str]]] | None = None):
        self.tables = tables or {}
        self.reference_ranges = self._index_ranges(self.tables.get("REFERENCE_RANGES", []))
        self.dm_sites = {r.get("USUBJID", ""): r.get("SITEID", "") for r in self.tables.get("DM", [])}

    @staticmethod
    def _index_ranges(rows: list[dict[str, str]]) -> dict[tuple[str, str, str], tuple[float, float]]:
        result: dict[tuple[str, str, str], tuple[float, float]] = {}
        for row in rows:
            try:
                test = (row.get("LBTESTCD") or row.get("TESTCD") or "").upper()
                unit = row.get("UNIT", "")
                lab = (row.get("LAB") or "CENTRAL").upper()
                result[(test, unit, lab)] = (float(row["LOW"]), float(row["HIGH"]))
            except (KeyError, TypeError, ValueError):
                continue
        return result

    @staticmethod
    def from_csv_texts(files: dict[str, str]) -> "AtlasEngine":
        tables: dict[str, list[dict[str, str]]] = {}
        for name, text in files.items():
            stem = name.rsplit("/", 1)[-1].rsplit(".", 1)[0].upper()
            tables[stem] = list(csv.DictReader(io.StringIO(text)))
        return AtlasEngine(tables)

    @staticmethod
    def _num(value: Any) -> float | None:
        if value is None:
            return None
        text = str(value).strip().upper()
        if not text or text in {"ND", "NA", "N/A", "BLANK"}:
            return None
        match = re.fullmatch(r"<?\s*(-?\d+(?:\.\d+)?)", text)
        return float(match.group(1)) if match else None

    @staticmethod
    def _date(value: str | None) -> datetime | None:
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
            try:
                return datetime.strptime(value[:19], fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _ref(domain: str, row: dict[str, str], fallback: int) -> str:
        seq = row.get(f"{domain}SEQ") or str(fallback)
        return f"{domain}|{row.get('USUBJID', '')}|{seq}"

    def summary(self) -> dict[str, Any]:
        dm = self.tables.get("DM", [])
        return {
            "subjects": len({r.get("USUBJID") for r in dm if r.get("USUBJID")}),
            "sites": len({r.get("SITEID") for r in dm if r.get("SITEID")}),
            "domains": {k: len(v) for k, v in self.tables.items()},
            "safety_signals": len(self.safety_signals()),
        }

    def _corrected_rows(self, rows: list[dict[str, str]]) -> list[tuple[int, dict[str, str]]]:
        """Keep the latest available correction for each domain/subject/sequence."""
        corrections = self.tables.get("CORRECTIONS", [])
        latest: dict[tuple[str, str, str], tuple[str, dict[str, str]]] = {}
        for correction in corrections:
            domain = (correction.get("DOMAIN") or "LB").upper()
            subject = correction.get("USUBJID", "")
            seq = correction.get("SEQ") or correction.get(f"{domain}SEQ", "")
            key = (domain, subject, seq)
            stamp = correction.get("CORRECTED_AT") or correction.get("DATETIME") or correction.get("CUT") or "0"
            latest[key] = max(latest.get(key, ("", {})), (stamp, correction), key=lambda item: item[0])
        output = []
        for index, row in enumerate(rows, 1):
            key = ("LB", row.get("USUBJID", ""), row.get("LBSEQ", str(index)))
            correction = latest.get(key)
            if correction:
                merged = dict(row)
                for source, target in (("LBORRES", "LBORRES"), ("VALUE", "LBORRES"), ("LBORRESU", "LBORRESU"), ("UNIT", "LBORRESU")):
                    if correction[1].get(source) not in (None, ""):
                        merged[target] = correction[1][source]
                output.append((index, merged))
            else:
                output.append((index, row))
        return output

    def safety_signals(self) -> list[dict[str, Any]]:
        signals: list[dict[str, Any]] = []
        for index, row in self._corrected_rows(self.tables.get("LB", [])):
            subject = row.get("USUBJID", "")
            site = self.dm_sites.get(subject, "")
            if site in self.EXCLUDED_SITES:
                continue
            value = self._num(row.get("LBORRES"))
            if value is None:
                continue
            test = (row.get("LBTESTCD") or row.get("LBTEST") or "").upper()
            unit = row.get("LBORRESU") or row.get("UNIT") or ""
            normalized = unit
            converted = value
            if test in {"ALT", "AST"} and unit in self.UNIT_CONVERSIONS:
                converted = value * self.UNIT_CONVERSIONS[unit]
                normalized = "U/L"
            lab = (row.get("LAB") or "CENTRAL").upper()
            bounds = self.reference_ranges.get((test, normalized, lab))
            if bounds is None:
                bounds = self.reference_ranges.get((test, normalized, "CENTRAL"))
            if bounds and not bounds[0] <= converted <= bounds[1]:
                signals.append({
                    "type": "laboratory_out_of_range",
                    "subject": subject,
                    "site": site,
                    "test": test,
                    "value": converted,
                    "unit": normalized,
                    "reference": {"low": bounds[0], "high": bounds[1]},
                    "evidence": [Evidence("LB", self._ref("LB", row, index), "Value outside applicable reference range").as_dict()],
                })
        return signals

    def query(self, question: str) -> dict[str, Any]:
        q = question.lower().strip()
        if any(x in q for x in ("how many subjects", "subject count", "enrolled")):
            return {"answer": f"{self.summary()['subjects']} unique subjects are present in the DM dataset.", "confidence": "high", "evidence": []}
        if "site" in q and ("how many" in q or "count" in q):
            return {"answer": f"{self.summary()['sites']} distinct sites are present in the DM dataset.", "confidence": "high", "evidence": []}
        if any(x in q for x in ("safety", "lab", "laboratory", "out of range", "hy's law")):
            findings = self.safety_signals()
            return {"answer": f"{len(findings)} potential laboratory out-of-range records were detected after applying protocol rules.", "confidence": "high", "evidence": [f["evidence"][0] for f in findings], "findings": findings[:100]}
        return {"answer": "No deterministic intent matched this question.", "confidence": "low", "evidence": [], "needs_review": True}
