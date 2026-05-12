from datetime import date

from app.coding_pipeline import suggest_codes


def test_suggest_codes_returns_core_code_systems():
    result = suggest_codes(
        "Patient has Type 2 Diabetes on Metformin. HbA1c today 7.8%. EKG shows ST elevation.",
        date(2024, 1, 22),
    )

    code_systems = {candidate["code_system"] for candidate in result["code_candidates"]}

    assert "ICD-10-CM" in code_systems
    assert "LOINC" in code_systems
    assert "RxNorm" in code_systems
    assert "CPT" in code_systems


def test_phi_detection_flags_mrn():
    result = suggest_codes("MRN: ABC12345. Patient denies chest pain.", date(2024, 1, 22))

    assert result["risk_summary"]["phi_risk_count"] == 1
    assert result["phi_findings"][0]["type"] == "possible_mrn"
