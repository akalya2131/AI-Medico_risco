from __future__ import annotations

from uuid import uuid4

from risk_engine import calculate_risk


DISEASE_HISTORY_MAP = {
    "Diabetes": "Type 2 Diabetes",
    "Heart Disease": "Heart Failure",
    "COPD": "COPD",
    "Hypertension": "Hypertension",
    "Cancer": "Cancer",
    "Asthma": "Asthma",
    "Kidney Disease": "CKD",
}

DISEASE_WEIGHTS = {
    "Diabetes": 12,
    "Heart Disease": 22,
    "COPD": 18,
    "Hypertension": 10,
    "Cancer": 25,
    "Asthma": 8,
    "Kidney Disease": 20,
}


def analyze_patient_input(payload: dict) -> dict:
    age = int(payload.get("age", 0) or 0)
    bmi = float(payload.get("bmi", 0) or 0)
    smoking = parse_smoking_status(payload.get("smoking_status"))
    disease = payload.get("disease", "Diabetes")
    claim_amount = float(payload.get("claim_amount", 0) or 0)
    claim_frequency = int(payload.get("claim_frequency", 0) or 0)

    contributions = [
        {"feature": "Age", "value": round(_clamp((age - 18) * 0.5, 0, 20), 1)},
        {"feature": "BMI", "value": 20 if bmi >= 30 else 10 if bmi >= 25 else 4},
        {"feature": "Smoking", "value": 18 if smoking else 0},
        {"feature": "Disease Severity", "value": DISEASE_WEIGHTS.get(disease, 10)},
        {"feature": "Claim Frequency", "value": _clamp(claim_frequency * 4, 0, 17)},
        {"feature": "Claim Amount", "value": 10 if claim_amount >= 200000 else 6 if claim_amount >= 75000 else 2},
    ]

    risk_score = min(100, round(sum(item["value"] for item in contributions)))
    risk_level = "Low" if risk_score <= 40 else "Medium" if risk_score <= 70 else "High"
    insights = build_insights(age, bmi, smoking, disease, claim_frequency, claim_amount)
    recommendations = build_recommendations(risk_level, smoking, bmi, disease)
    validation_hints = build_validation_hints(age, bmi, claim_amount, claim_frequency, smoking)
    risk_color = {"Low": "emerald", "Medium": "amber", "High": "rose"}[risk_level]

    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "insights": insights,
        "contributions": contributions,
        "recommendations": recommendations,
        "validation_hints": validation_hints,
        "risk_color": risk_color,
    }


def build_patient_payload(payload: dict) -> dict:
    smoking = parse_smoking_status(payload.get("smoking_status"))
    disease = payload.get("disease", "Diabetes")
    canonical_disease = DISEASE_HISTORY_MAP.get(disease, disease)
    claim_amount = float(payload.get("claim_amount", 0) or 0)
    claim_frequency = int(payload.get("claim_frequency", 0) or 0)

    medical_history = [canonical_disease]
    if smoking:
        medical_history.append("Smoking")

    claims = [
        {
            "claim_id": f"CLM-{uuid4().hex[:6].upper()}",
            "provider": "AI Intake",
            "amount_inr": claim_amount,
            "status": "New",
            "diagnosis_codes": [canonical_disease],
            "date": payload.get("claim_date", "") or "2026-03-21",
        }
        for _ in range(max(0, claim_frequency))
    ]

    ai_analysis = analyze_patient_input(payload)
    risk_engine_payload = {
        "medical_history": medical_history,
        "claims": claims,
        "bmi": float(payload.get("bmi", 0) or 0),
    }
    initial_risk = calculate_risk(risk_engine_payload)

    return {
        "full_name": payload.get("patient_name", "").strip(),
        "age": int(payload.get("age", 0) or 0),
        "gender": payload.get("gender", ""),
        "city": payload.get("city", "Care Hub").strip() or "Care Hub",
        "primary_diagnosis": disease,
        "disease": disease,
        "medical_history": medical_history,
        "claims": claims,
        "claim_amount": claim_amount,
        "claim_frequency": claim_frequency,
        "smoking_status": smoking,
        "timeline": [],
        "documents": [],
        "lat": 20.5937,
        "lng": 78.9629,
        "bmi": float(payload.get("bmi", 0) or 0),
        "ai_analysis": ai_analysis,
        "risk_score": initial_risk["risk_score"],
        "risk_label": initial_risk["risk_label"],
        "preventive_care_steps": initial_risk["preventive_care_steps"],
    }


def derive_ai_analysis_from_patient(patient: dict) -> dict:
    payload = {
        "age": patient.get("age", 0),
        "bmi": patient.get("bmi", 0),
        "smoking_status": "Yes" if any(str(item).lower() == "smoking" for item in patient.get("medical_history", [])) else "No",
        "disease": patient.get("primary_diagnosis") or patient.get("disease") or "Diabetes",
        "claim_amount": sum(float(claim.get("amount_inr", 0) or 0) for claim in patient.get("claims", [])),
        "claim_frequency": len(patient.get("claims", [])),
    }
    return analyze_patient_input(payload)


def parse_smoking_status(value) -> bool:
    return str(value).strip().lower() in {"yes", "true", "1", "on"}


def build_insights(age: int, bmi: float, smoking: bool, disease: str, claim_frequency: int, claim_amount: float) -> list[str]:
    insights = []
    if age >= 60:
        insights.append("Advanced age is increasing baseline care complexity.")
    if bmi >= 30:
        insights.append("High BMI is increasing metabolic and cardiovascular risk.")
    elif bmi >= 25:
        insights.append("Elevated BMI is contributing to moderate risk.")
    if smoking:
        insights.append("Smoking habit is raising respiratory and chronic-disease risk.")
    if disease in {"Heart Disease", "COPD", "Cancer", "Kidney Disease"}:
        insights.append("Chronic disease severity is a major driver of the score.")
    if claim_frequency >= 4:
        insights.append("Frequent claims suggest ongoing instability or repeated interventions.")
    if claim_amount >= 200000:
        insights.append("High claim amount indicates elevated utilization and case severity.")
    return insights or ["Current profile suggests a relatively stable baseline with preventive monitoring needs."]


def build_recommendations(risk_level: str, smoking: bool, bmi: float, disease: str) -> list[str]:
    recommendations = [
        "Immediate specialist review within 48 hours." if risk_level == "High"
        else "Focused clinical follow-up and care-plan review." if risk_level == "Medium"
        else "Routine preventive monitoring and follow-up scheduling.",
        "Enroll in smoking cessation counselling." if smoking else "Maintain healthy lifestyle coaching and adherence support.",
        "Start structured weight-management and nutrition support." if bmi >= 30 else "Continue BMI trend monitoring.",
    ]
    if disease == "Kidney Disease":
        recommendations.append("Order renal function monitoring and nephrology review.")
    elif disease == "Heart Disease":
        recommendations.append("Arrange cardiology medication reconciliation and echocardiogram review.")
    return recommendations[:4]


def build_validation_hints(age: int, bmi: float, claim_amount: float, claim_frequency: int, smoking: bool) -> list[str]:
    hints = []
    if age < 18:
        hints.append("Age is unusually low for standard adult risk analysis.")
    if bmi >= 30:
        hints.append("BMI indicates obesity risk; consider preventive counselling.")
    if claim_amount >= 200000:
        hints.append("Large claim amount suggests a high-acuity care episode.")
    if claim_frequency >= 4:
        hints.append("Frequent claims may indicate chronic instability.")
    if smoking:
        hints.append("Smoking materially increases respiratory and cardiovascular risk.")
    return hints


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))
