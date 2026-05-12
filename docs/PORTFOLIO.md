# Portfolio Case Study: Clinical Coder Pro

## Problem

Hospital coding teams review dense clinical notes and must identify diagnosis, symptom, procedure, laboratory, and medication codes with evidence. Manual review is time-consuming, and fully automated coding is risky because coding requires context, official guidelines, payer rules, and human accountability.

## Solution

Clinical Coder Pro is a local prototype that converts a raw clinical note into candidate coding suggestions for human coder review. It focuses on evidence transparency, reviewer workflow, and compliance readiness rather than black-box automation.

## Product Highlights

- Candidate ICD-10-CM, CPT, LOINC, and RxNorm suggestions
- Evidence spans highlighted directly in the note
- Confidence, negation, and code-range risk indicators
- Approve, reject, and needs-review workflow
- Local audit trail and review export
- PHI pattern flags for simple MRN, phone, email, and SSN patterns
- Compliance readiness panel for production controls

## Technical Stack

- Python
- FastAPI
- Pydantic
- Vanilla HTML, CSS, and JavaScript
- Deterministic clinical NLP rules for a transparent prototype

## Responsible AI and Compliance Position

This project is intentionally designed as coder-assistive software. It does not claim autonomous billing accuracy or legal compliance by default. Production deployment would require licensed/current code sets, HIPAA security controls, business associate agreement review when PHI is involved, audit retention, authentication, encryption, validation against coder-labeled data, and formal legal/security review.

## Next Commercial Milestones

- Replace seed rules with official code-set ingestion and search
- Add database persistence with encrypted audit logs
- Add SSO, MFA, role-based permissions, and tenant isolation
- Add coder-labeled evaluation reports
- Add FHIR/EHR integration layer
- Add deployment architecture for hospital cloud or VPC environments
