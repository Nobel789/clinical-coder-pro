# Clinical Coder Pro

Clinical Coder Pro is a portfolio-ready healthcare NLP prototype that turns raw clinical notes into candidate coding suggestions for human coder review.

The app is designed around a responsible coding workflow: evidence first, reviewer control, auditability, and compliance readiness. It does not claim autonomous billing accuracy or legal compliance out of the box.

## What It Does

- Extracts clinical concepts from synthetic clinical notes
- Suggests candidate ICD-10-CM, CPT, LOINC, and RxNorm codes
- Highlights evidence spans in the note
- Flags negated context, low-confidence candidates, code ranges, and simple PHI patterns
- Lets coders approve, reject, or keep suggestions in review
- Generates a local audit trail and JSON review export
- Shows production controls needed for HIPAA-oriented deployment

## Demo Workflow

1. Paste or load a sample clinical note.
2. Run analysis.
3. Review candidate codes by code system.
4. Inspect evidence and risk badges.
5. Approve, reject, or keep items in review.
6. Export the reviewed result as JSON.

## Tech Stack

- Python
- FastAPI
- Pydantic
- Vanilla HTML, CSS, and JavaScript
- Deterministic NLP rules for transparent prototype behavior

## Run Locally

```powershell
cd "c:\Users\nobel\Desktop\Open_AI_Coddex\clinical_coder_mvp"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000
```

For a fresh setup:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## API Example

```powershell
$body = @{
  raw_note_text = "Patient has Type 2 Diabetes on Metformin. HbA1c today 7.8%. EKG shows ST elevation."
  note_date = "2024-01-22"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/api/suggest-codes" `
  -ContentType "application/json" `
  -Body $body
```

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Project Structure

```text
clinical_coder_mvp/
  app/
    coding_pipeline.py
    main.py
  static/
    index.html
    app.js
    styles.css
  docs/
    PORTFOLIO.md
  tests/
    test_coding_pipeline.py
```

## Compliance Boundary

This is a local prototype and should use synthetic or de-identified notes only.

Before production use with PHI, a real implementation needs current licensed code sets, validation against coder-labeled data, role-based access control, SSO/MFA, encryption in transit and at rest, immutable audit logging, retention/deletion policies, deployment review, and a business associate agreement when serving covered entities.

## Portfolio Case Study

See [docs/PORTFOLIO.md](docs/PORTFOLIO.md) for a concise product and technical case study.
