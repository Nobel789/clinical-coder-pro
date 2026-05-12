from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


ABBREVIATIONS = {
    "pt": "patient",
    "htn": "hypertension",
    "bp": "blood pressure",
    "ekg": "electrocardiogram",
    "ecg": "electrocardiogram",
    "sob": "shortness of breath",
    "bid": "twice daily",
    "ed": "emergency department",
    "dm2": "type 2 diabetes",
    "t2dm": "type 2 diabetes",
    "mi": "myocardial infarction",
}


NEGATION_PATTERNS = [
    r"\bdenies?\s+{term}\b",
    r"\bno\s+(?:evidence\s+of\s+)?{term}\b",
    r"\bwithout\s+{term}\b",
    r"\bnegative\s+for\s+{term}\b",
]

PHI_PATTERNS = {
    "possible_mrn": r"\b(?:MRN|Medical Record Number)\s*[:#]?\s*[A-Z0-9-]{5,}\b",
    "possible_phone": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]\d{3}[-.\s]\d{4}\b",
    "possible_email": r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    "possible_ssn": r"\b\d{3}-\d{2}-\d{4}\b",
}

COMPLIANCE_POSTURE = {
    "mode": "local_prototype",
    "phi_storage": "not_persisted_by_application",
    "human_review_required": True,
    "baa_required_for_phi_use": True,
    "security_controls_needed_for_production": [
        "role based access control",
        "single sign on and MFA",
        "encryption in transit and at rest",
        "complete audit logging",
        "retention and deletion policy",
        "vendor risk review and business associate agreement",
        "current licensed code set management",
    ],
}


@dataclass(frozen=True)
class ConceptRule:
    concept: str
    category: str
    patterns: tuple[str, ...]
    evidence_label: str
    code_system: str
    code: str
    description: str
    coding_note: str
    negation_sensitive: bool = True


RULES: tuple[ConceptRule, ...] = (
    ConceptRule(
        concept="type_2_diabetes",
        category="diagnosis",
        patterns=(r"\btype\s*2\s+diabetes\b", r"\bt2dm\b", r"\bdm2\b"),
        evidence_label="Type 2 diabetes",
        code_system="ICD-10-CM",
        code="E11.9",
        description="Type 2 diabetes mellitus without complications",
        coding_note="Candidate only. Confirm complications, insulin use, control status, and encounter context.",
    ),
    ConceptRule(
        concept="hypertension",
        category="diagnosis",
        patterns=(r"\bhypertension\b", r"\bhtn\b"),
        evidence_label="hypertension",
        code_system="ICD-10-CM",
        code="I10",
        description="Essential hypertension",
        coding_note="Candidate only. Confirm provider-documented diagnosis and related conditions.",
    ),
    ConceptRule(
        concept="chest_pain",
        category="symptom",
        patterns=(r"\bchest\s+pain\b",),
        evidence_label="chest pain",
        code_system="ICD-10-CM",
        code="R07.9",
        description="Chest pain, unspecified",
        coding_note="Candidate only. Do not code symptom if a definitive related diagnosis supersedes it.",
    ),
    ConceptRule(
        concept="shortness_of_breath",
        category="symptom",
        patterns=(r"\bshortness\s+of\s+breath\b", r"\bdyspnea\b", r"\bsob\b"),
        evidence_label="shortness of breath",
        code_system="ICD-10-CM",
        code="R06.02",
        description="Shortness of breath",
        coding_note="Candidate only. Confirm symptom is current and clinically relevant.",
    ),
    ConceptRule(
        concept="abnormal_ekg",
        category="finding",
        patterns=(r"\bst\s+elevation\b", r"\babnormal\s+(?:ekg|ecg|electrocardiogram)\b"),
        evidence_label="ST elevation / abnormal electrocardiogram",
        code_system="ICD-10-CM",
        code="R94.31",
        description="Abnormal electrocardiogram",
        coding_note="Candidate only. Confirm final interpretation and related diagnosis.",
    ),
    ConceptRule(
        concept="electrocardiogram",
        category="procedure_or_test",
        patterns=(r"\b(?:ekg|ecg|electrocardiogram)\b",),
        evidence_label="electrocardiogram",
        code_system="CPT",
        code="93000/93005/93010",
        description="Electrocardiogram candidates",
        coding_note="Candidate range. Exact CPT depends on tracing, interpretation, report, setting, and payer rules.",
        negation_sensitive=False,
    ),
    ConceptRule(
        concept="hba1c",
        category="laboratory",
        patterns=(r"\bhba1c\b", r"\bhemoglobin\s+a1c\b"),
        evidence_label="HbA1c",
        code_system="LOINC",
        code="4548-4",
        description="Hemoglobin A1c/Hemoglobin.total in Blood",
        coding_note="Candidate only. Confirm specimen, method, and local lab catalog mapping.",
        negation_sensitive=False,
    ),
    ConceptRule(
        concept="metformin",
        category="medication",
        patterns=(r"\bmetformin\b",),
        evidence_label="Metformin",
        code_system="RxNorm",
        code="6809",
        description="Metformin",
        coding_note="Ingredient candidate. Confirm dose, route, frequency, and medication status.",
        negation_sensitive=False,
    ),
    ConceptRule(
        concept="lisinopril",
        category="medication",
        patterns=(r"\blisinopril\b",),
        evidence_label="Lisinopril",
        code_system="RxNorm",
        code="29046",
        description="Lisinopril",
        coding_note="Ingredient candidate. Confirm dose, route, frequency, and medication status.",
        negation_sensitive=False,
    ),
    ConceptRule(
        concept="aspirin",
        category="medication",
        patterns=(r"\baspirin\b",),
        evidence_label="Aspirin",
        code_system="RxNorm",
        code="1191",
        description="Aspirin",
        coding_note="Ingredient candidate. Administration coding depends on setting and documentation.",
        negation_sensitive=False,
    ),
)


def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    normalized = clean_text(text).lower()
    for abbreviation, full_form in ABBREVIATIONS.items():
        normalized = re.sub(rf"\b{re.escape(abbreviation)}\b", full_form, normalized)
    return normalized


def tokenize_text(text: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9/%.-]+", text)


def _is_negated(normalized_text: str, evidence: str) -> bool:
    escaped = re.escape(evidence.lower()).replace(r"\ ", r"\s+")
    return any(re.search(pattern.format(term=escaped), normalized_text) for pattern in NEGATION_PATTERNS)


def _find_evidence(text: str, patterns: tuple[str, ...]) -> dict[str, Any] | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return {
                "text": match.group(0),
                "start": match.start(),
                "end": match.end(),
            }
    return None


def extract_time_expressions(text: str, note_date: date) -> list[dict[str, str]]:
    clean = clean_text(text)
    phrases = {
        "today": note_date.isoformat(),
        "immediately": f"{note_date.isoformat()} same day / immediate",
    }
    results = []
    for phrase, normalized in phrases.items():
        if re.search(rf"\b{re.escape(phrase)}\b", clean, flags=re.IGNORECASE):
            results.append({"time_text": phrase, "normalized_time": normalized})

    relative_patterns = [
        (r"\b(?:in|return in|follow up in)\s+(\d+)\s+weeks?\b", "future weeks"),
        (r"\bin\s+(\d+)\s+months?\b", "future months"),
        (r"\b(\d+)\s+months?\s+ago\b", "past months"),
        (r"\blast\s+week\b", "past week"),
    ]
    for pattern, meaning in relative_patterns:
        for match in re.finditer(pattern, clean, flags=re.IGNORECASE):
            results.append({"time_text": match.group(0), "normalized_time": meaning})
    return results


def extract_entities(text: str) -> list[dict[str, Any]]:
    entities = []
    for rule in RULES:
        evidence = _find_evidence(text, rule.patterns)
        if evidence:
            entities.append(
                {
                    "text": evidence["text"],
                    "label": rule.category,
                    "start": evidence["start"],
                    "end": evidence["end"],
                    "confidence": 0.86,
                }
            )
    return entities


def detect_phi_risks(text: str) -> list[dict[str, Any]]:
    findings = []
    for label, pattern in PHI_PATTERNS.items():
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            findings.append(
                {
                    "type": label,
                    "start": match.start(),
                    "end": match.end(),
                    "text": match.group(0),
                    "severity": "high",
                }
            )
    return findings


def summarize_candidate_risk(candidates: list[dict[str, Any]], phi_findings: list[dict[str, Any]]) -> dict[str, Any]:
    negated_count = sum(1 for item in candidates if item["negated"])
    low_confidence_count = sum(1 for item in candidates if item["confidence"] < 0.7)
    exact_code_count = sum(1 for item in candidates if "/" not in item["code"])
    review_load = negated_count + low_confidence_count + sum(1 for item in candidates if "/" in item["code"])

    return {
        "candidate_count": len(candidates),
        "exact_code_count": exact_code_count,
        "requires_review_count": len(candidates),
        "low_confidence_count": low_confidence_count,
        "negated_context_count": negated_count,
        "phi_risk_count": len(phi_findings),
        "estimated_review_load": "high" if review_load >= 3 else "moderate" if review_load else "low",
    }


def suggest_codes(raw_note_text: str, note_date: date | None = None) -> dict[str, Any]:
    resolved_date = note_date or datetime.utcnow().date()
    clean = clean_text(raw_note_text)
    normalized = normalize_text(clean)
    tokens = tokenize_text(clean)
    entities = extract_entities(clean)
    time_expressions = extract_time_expressions(clean, resolved_date)
    phi_findings = detect_phi_risks(clean)

    candidates = []
    for rule in RULES:
        evidence = _find_evidence(clean, rule.patterns)
        if not evidence:
            continue

        normalized_evidence = normalize_text(evidence["text"])
        negated = rule.negation_sensitive and _is_negated(normalized, normalized_evidence)
        confidence = 0.35 if negated else 0.82
        candidates.append(
            {
                "id": f"{rule.code_system}:{rule.code}:{evidence['start']}",
                "concept": rule.concept,
                "category": rule.category,
                "code_system": rule.code_system,
                "code": rule.code,
                "description": rule.description,
                "evidence": evidence,
                "negated": negated,
                "confidence": confidence,
                "needs_coder_review": True,
                "status": "needs_review",
                "coding_note": rule.coding_note,
                "validation_reason": "Negated context detected." if negated else "Evidence found in note.",
            }
        )

    risk_summary = summarize_candidate_risk(candidates, phi_findings)

    return {
        "product": "Clinical Coder Pro Prototype",
        "note_date": resolved_date.isoformat(),
        "processed_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "clean_text": clean,
        "normalized_text": normalized,
        "tokens": tokens,
        "entities": entities,
        "time_expressions": time_expressions,
        "phi_findings": phi_findings,
        "risk_summary": risk_summary,
        "code_candidates": candidates,
        "compliance_posture": COMPLIANCE_POSTURE,
        "warnings": [
            "Coder review is required before billing or reporting.",
            "This local prototype does not persist PHI, but production use requires formal HIPAA/security review.",
            "Use current official or licensed code sets before production billing use.",
        ],
    }
