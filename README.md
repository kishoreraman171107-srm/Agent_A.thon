# ATLAS — Clinical Trial Intelligence Platform

A fresh, evidence-first clinical trial intelligence platform designed for the hackathon. The project combines a modern dashboard experience with a deterministic analysis workflow.

## Current website

The responsive frontend includes:
- Clinical trial overview with enrollment, sites, safety signals, and evidence coverage
- Evidence Explorer with demo question answering
- Safety signal review queue
- Protocol amendment timeline
- CDISC domain health cards
- CSV/JSON import entry point
- Exportable trial summary
- Responsive layout for desktop and mobile

## Planned intelligence layer

- Normalize CDISC domains such as DM, AE, LB, VS, EX, and SV
- Build a deterministic evidence graph
- Support count, lookup, finding, and trap questions
- Convert units and normalize date formats
- Provide exact record-level evidence references
- Track protocol amendments and medical monitor decisions
- Add rule-based safety prioritization and audit trails

## Run locally

Open `index.html` in a browser, or serve the directory with:

```bash
python -m http.server 8000
```

Then visit `http://localhost:8000`.

## Important

The current interface uses clearly labeled demo responses. It is not a clinical decision-making system and must be connected to validated backend data before real-world use.
