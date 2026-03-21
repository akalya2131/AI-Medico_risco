from __future__ import annotations

from collections import Counter, defaultdict

from app.utils.geo import closest_hospital
from risk_engine import calculate_risk


def enrich_patients(patients: list[dict], hospitals: list[dict]) -> list[dict]:
    enriched_patients = []
    for patient in patients:
        prediction = calculate_risk(patient)
        nearest = closest_hospital(patient, hospitals) if prediction["risk_score"] >= 4 else None
        enriched_patients.append(
            {
                **patient,
                "risk": prediction,
                "closest_hospital": nearest,
                "is_high_risk": prediction["risk_score"] >= 4,
            }
        )
    return enriched_patients


def get_high_risk_patients(patients: list[dict]) -> list[dict]:
    return [patient for patient in patients if patient.get("risk", {}).get("risk_score", 0) >= 4]


def build_dashboard_stats(patients: list[dict]) -> dict:
    total_patients = len(patients)
    total_risk = sum(patient["risk"]["risk_score"] for patient in patients)
    average_risk = round(total_risk / total_patients, 1) if total_patients else 0
    total_claims_inr = 0
    high_risk_patients = get_high_risk_patients(patients)
    risk_distribution = {"Stable": 0, "Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    claims_trend: dict[str, float] = defaultdict(float)

    for patient in patients:
        risk_distribution[patient["risk"]["risk_label"]] += 1
        for claim in patient.get("claims", []):
            total_claims_inr += float(claim.get("amount_inr", 0) or 0)
            claims_trend[str(claim.get("date", "Unknown"))[:7]] += float(claim.get("amount_inr", 0) or 0)

    ordered_trend = [{"month": month, "amount_inr": round(amount, 2)} for month, amount in sorted(claims_trend.items())]
    return {
        "total_patients": total_patients,
        "average_risk": average_risk,
        "total_claims_inr": round(total_claims_inr, 2),
        "high_risk_alerts": len(high_risk_patients),
        "risk_distribution": risk_distribution,
        "claims_trend": ordered_trend,
    }


def build_analytics_summary(patients: list[dict]) -> dict:
    disease_counts: Counter[str] = Counter()
    risk_distribution = {str(score): 0 for score in range(1, 6)}

    for patient in patients:
        risk_distribution[str(patient["risk"]["risk_score"])] += 1
        for disease in _extract_disease_terms(patient):
            disease_counts[disease] += 1

    return {
        "disease_counts": dict(sorted(disease_counts.items(), key=lambda item: (-item[1], item[0]))),
        "risk_distribution": risk_distribution,
    }


def _extract_disease_terms(patient: dict) -> list[str]:
    disease_terms = []
    disease_terms.extend(_normalize_values(patient.get("primary_diagnosis")))
    disease_terms.extend(_normalize_values(patient.get("medical_history", [])))

    for claim in patient.get("claims", []):
        if isinstance(claim, dict):
            disease_terms.extend(_normalize_values(claim.get("diagnosis_codes", [])))

    return sorted(set(disease_terms))


def _normalize_values(values) -> list[str]:
    if values in (None, ""):
        return []

    if isinstance(values, str):
        values = values.replace(";", ",").split(",")
    elif not isinstance(values, list):
        values = [values]

    normalized = []
    for value in values:
        if value in (None, ""):
            continue
        normalized.extend(part.strip().lower() for part in str(value).replace(";", ",").split(",") if part.strip())
    return normalized
