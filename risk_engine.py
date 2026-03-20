from __future__ import annotations

from typing import Any

RISK_RULES = [
    (5, {"ckd", "chronic kidney disease", "stroke", "heart failure"}),
    (4, {"copd", "diabetes", "type 2 diabetes", "cad", "coronary artery disease"}),
    (3, {"hypertension", "asthma", "smoking", "obesity"}),
    (2, {"thyroid", "allergies", "allergy"}),
]

RISK_LABELS = {1: "Stable", 2: "Low", 3: "Moderate", 4: "High", 5: "Critical"}

PREVENTIVE_LIBRARY = {
    "diabetes": [
        "Quarterly HbA1c test",
        "Diabetic foot exam",
        "Nutrition review for glucose control",
    ],
    "ckd": [
        "Renal function panel every quarter",
        "Urine albumin screening",
        "Nephrology medication review",
    ],
    "heart failure": [
        "Echocardiogram follow-up",
        "Daily weight and fluid monitoring",
        "Cardiology medication reconciliation",
    ],
    "stroke": [
        "Neurology follow-up",
        "Mobility and swallow reassessment",
        "Blood pressure control review",
    ],
    "copd": [
        "Pulmonary function test",
        "Smoking cessation counselling",
        "Vaccination review for respiratory protection",
    ],
    "cad": [
        "Lipid profile monitoring",
        "Cardiology review",
        "Exercise tolerance assessment",
    ],
    "hypertension": [
        "Home blood pressure log",
        "Kidney function monitoring",
        "DASH diet coaching",
    ],
    "asthma": [
        "Inhaler technique review",
        "Annual spirometry",
        "Trigger avoidance coaching",
    ],
    "allergies": [
        "Allergen diary review",
        "Rescue medication check",
        "Seasonal trigger counselling",
    ],
}

GENERIC_PREVENTIVE_STEPS = [
    "Medication reconciliation with the care team",
    "Lifestyle counselling and annual preventive screening",
    "Follow-up review with the primary physician",
]


def calculate_risk(patient_data: dict[str, Any]) -> dict[str, Any]:
    history_terms = _extract_history_terms(patient_data)
    diagnosis_terms = _extract_diagnosis_terms(patient_data)
    bmi = _to_float(patient_data.get("bmi"))
    claim_count = _extract_claim_count(patient_data)

    base_score = 1
    matched_conditions: list[str] = []

    for score, conditions in RISK_RULES:
        hits = sorted({term for term in history_terms if term in conditions})
        if hits:
            base_score = max(base_score, score)
            matched_conditions.extend(hits)

    if bmi is not None and bmi > 30:
        base_score = max(base_score, 3)
        matched_conditions.append("bmi > 30")

    claim_penalty_applied = claim_count > 3
    risk_score = min(5, base_score + (1 if claim_penalty_applied else 0))
    preventive_steps = _build_preventive_steps(history_terms, diagnosis_terms, bmi)
    reasoning = _build_reasoning(risk_score, matched_conditions, claim_penalty_applied)

    return {
        "risk_score": risk_score,
        "risk_label": RISK_LABELS[risk_score],
        "reasoning": reasoning,
        "claim_count": claim_count,
        "claim_penalty_applied": claim_penalty_applied,
        "matched_conditions": sorted(set(matched_conditions)),
        "history_terms_analyzed": history_terms,
        "preventive_care_steps": preventive_steps,
        "preventive_care": preventive_steps,
    }


def _build_reasoning(risk_score: int, matched_conditions: list[str], claim_penalty_applied: bool) -> str:
    if matched_conditions:
        driver = ", ".join(sorted(set(matched_conditions[:3])))
        message = f"Risk is {risk_score}/5 because of {driver}."
    else:
        message = f"Risk is {risk_score}/5 because no major chronic history was detected."

    if claim_penalty_applied:
        message += " More than three insurance claims increased the score by one level."
    return message


def _build_preventive_steps(history_terms: list[str], diagnosis_terms: list[str], bmi: float | None) -> list[str]:
    combined_terms = diagnosis_terms + history_terms
    steps: list[str] = []

    for term in combined_terms:
        for suggestion in PREVENTIVE_LIBRARY.get(term, []):
            if suggestion not in steps:
                steps.append(suggestion)

    if ("diabetes" in combined_terms or "type 2 diabetes" in combined_terms) and bmi is not None and bmi > 30:
        custom = "Suggest DASH Diet with structured weight-loss coaching"
        if custom not in steps:
            steps.insert(0, custom)

    if not steps:
        steps.extend(GENERIC_PREVENTIVE_STEPS)

    while len(steps) < 3:
        for generic in GENERIC_PREVENTIVE_STEPS:
            if generic not in steps:
                steps.append(generic)
            if len(steps) == 3:
                break

    return steps[:3]


def _extract_history_terms(patient_data: dict[str, Any]) -> list[str]:
    terms: list[str] = []
    for key in ("medical_history", "history", "chronic_conditions", "diagnosis_codes"):
        terms.extend(_normalize_values(patient_data.get(key, [])))

    for claim in _extract_claims(patient_data):
        if isinstance(claim, dict):
            terms.extend(_normalize_values(claim.get("diagnosis_codes", [])))

    return sorted(set(terms))


def _extract_diagnosis_terms(patient_data: dict[str, Any]) -> list[str]:
    terms = _normalize_values(patient_data.get("diagnosis_codes", []))
    for claim in _extract_claims(patient_data):
        if isinstance(claim, dict):
            terms.extend(_normalize_values(claim.get("diagnosis_codes", [])))
    return sorted(set(terms))


def _extract_claims(patient_data: dict[str, Any]) -> list[Any]:
    for key in ("claims", "insurance_claims", "claim_history"):
        claims = patient_data.get(key, [])
        if isinstance(claims, list):
            return claims
    return []


def _extract_claim_count(patient_data: dict[str, Any]) -> int:
    explicit_count = patient_data.get("insurance_claims_count")
    if isinstance(explicit_count, int):
        return explicit_count

    claims = _extract_claims(patient_data)
    if claims:
        return len(claims)

    try:
        return int(explicit_count or 0)
    except (TypeError, ValueError):
        return 0


def _normalize_values(values: Any) -> list[str]:
    if values is None:
        return []
    if isinstance(values, str):
        values = values.replace(";", ",").split(",")
    if not isinstance(values, list):
        values = [values]

    normalized = []
    for value in values:
        if isinstance(value, str):
            normalized.extend(part.strip().lower() for part in value.replace(";", ",").split(",") if part.strip())
        else:
            normalized.append(str(value).strip().lower())
    return normalized


def _to_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None
