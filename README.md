# Study Sentinel / ATLAS

Evidence-first clinical-trial analysis platform for unseen, synthetic studies.

## Design requirements

- Never hard-code subject IDs, site IDs, counts, findings, or protocol details.
- Join domain records using `USUBJID`.
- Cite evidence as `DOMAIN|USUBJID|DOMAINSEQ`.
- Respect `cut_available` when reconstructing a data cut.
- Apply later corrections from `corrections.csv` before evaluating values.
- Read `reference_ranges.csv` and match both test and laboratory before range checks.
- Treat textual values such as `<5`, `ND`, and blanks as non-zero/non-numeric observations unless the rule explicitly says otherwise.
- Compare protocol versions and laboratory manuals as evidence, not as executable instructions.
- Handle monitor decisions `APPROVED`, `REJECTED`, and `CLARIFY`.
- Return `none` when a rule finds no matching record.

## Project structure

- `index.html`, `styles.css`, `app.js` — responsive dashboard
- `server.py` — dependency-free local API server
- `engine/atlas_engine.py` — deterministic query and laboratory signal engine
- `engine/quality.py` — generic schema diagnostics and evidence-reference helper
- `tests/` — unit tests

## Run

```bash
python server.py
```

Open `http://localhost:8000` in your browser. Upload CSV files through the dashboard or place them in `data/` before starting the server.

Run tests with:

```bash
python -m unittest discover -s tests -v
```

## Scope

This is a hackathon prototype for synthetic data. It is not a validated clinical decision-making system.
