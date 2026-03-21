from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from sklearn.ensemble import RandomForestClassifier

DISEASE_OPTIONS = ["Diabetes", "COPD", "Heart Disease", "Hypertension", "Cancer", "Asthma", "Kidney Disease"]
RISK_CLASSES = [1, 2, 3, 4, 5]


@dataclass
class ModelBundle:
    model: RandomForestClassifier
    feature_names: list[str]


def _has_smoking_history(patient: dict[str, Any]) -> int:
    smoking_status = str(patient.get("smoking_status", "")).strip().lower()
    if smoking_status in {"yes", "true", "1", "on"}:
        return 1

    history = patient.get("medical_history", []) or []
    return int(any(str(item).strip().lower() == "smoking" for item in history))


def _extract_disease(patient: dict[str, Any]) -> str:
    return str(patient.get("disease") or patient.get("primary_diagnosis") or "Diabetes")


def _extract_claim_count(patient: dict[str, Any]) -> int:
    claims = patient.get("claims")
    if isinstance(claims, list):
        return len(claims)
    return int(patient.get("claim_frequency", 0) or 0)


def _extract_claim_amount(patient: dict[str, Any]) -> float:
    claims = patient.get("claims")
    if isinstance(claims, list) and claims:
        return float(sum(float(claim.get("amount_inr", 0) or 0) for claim in claims))
    return float(patient.get("claim_amount", 0) or 0)


def _build_feature_vector(patient: dict[str, Any], feature_names: list[str]) -> list[float]:
    disease = _extract_disease(patient)
    features = {
        "Age": float(patient.get("age", 0) or 0),
        "BMI": float(patient.get("bmi", 0) or 0),
        "Number of Claims": float(_extract_claim_count(patient)),
        "Smoking": float(_has_smoking_history(patient)),
    }
    for disease_name in DISEASE_OPTIONS:
        features[f"Disease::{disease_name}"] = 1.0 if disease == disease_name else 0.0
    return [features.get(name, 0.0) for name in feature_names]


def _target_score(patient: dict[str, Any]) -> int:
    if patient.get("risk_score"):
        score = float(patient.get("risk_score") or 0)
        return int(max(1, min(5, round(score))))

    age = int(patient.get("age", 0) or 0)
    bmi = float(patient.get("bmi", 0) or 0)
    claims = _extract_claim_count(patient)
    claim_amount = _extract_claim_amount(patient)
    disease = _extract_disease(patient)

    score = 1
    if age >= 65:
        score += 1
    if bmi >= 30:
        score += 1
    if claims >= 3 or claim_amount >= 150000:
        score += 1
    if disease in {"COPD", "Cancer", "Heart Disease", "Kidney Disease"}:
        score += 1
    return max(1, min(5, score))


def _generate_synthetic_patients(row_count: int = 200) -> list[dict[str, Any]]:
    synthetic = []
    for _ in range(row_count):
        disease = random.choice(DISEASE_OPTIONS)
        age = random.randint(21, 88)
        bmi = round(random.uniform(18.0, 39.5), 1)
        claim_frequency = random.randint(0, 7)
        claim_amount = random.randint(0, 280000)
        smoking = random.random() < 0.3

        score = 1
        if age >= 65:
            score += 1
        if bmi >= 30:
            score += 1
        if claim_frequency >= 3 or claim_amount >= 140000:
            score += 1
        if smoking:
            score += 1
        if disease in {"COPD", "Cancer", "Heart Disease", "Kidney Disease"}:
            score += 1

        synthetic.append(
            {
                "age": age,
                "bmi": bmi,
                "claim_frequency": claim_frequency,
                "claim_amount": claim_amount,
                "disease": disease,
                "smoking_status": "Yes" if smoking else "No",
                "risk_score": max(1, min(5, score)),
            }
        )
    return synthetic


def train_model(patients: list[dict[str, Any]] | None = None) -> ModelBundle:
    records = patients or []
    if not records:
        records = _generate_synthetic_patients(200)

    feature_names = ["Age", "BMI", "Number of Claims", "Smoking"] + [f"Disease::{disease}" for disease in DISEASE_OPTIONS]
    x_train = [_build_feature_vector(patient, feature_names) for patient in records]
    y_train = [_target_score(patient) for patient in records]

    model = RandomForestClassifier(n_estimators=200, random_state=42)
    model.fit(x_train, y_train)
    return ModelBundle(model=model, feature_names=feature_names)


def predict_patient_risk(patient: dict[str, Any], training_patients: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    bundle = train_model(training_patients)
    row = [_build_feature_vector(patient, bundle.feature_names)]

    probabilities = bundle.model.predict_proba(row)[0]
    class_labels = [int(label) for label in bundle.model.classes_]
    weighted_score = sum(score * probability for score, probability in zip(class_labels, probabilities))
    predicted_score = int(max(1, min(5, round(weighted_score))))

    disease_importance = sum(
        importance
        for feature, importance in zip(bundle.feature_names, bundle.model.feature_importances_)
        if feature.startswith("Disease::")
    )
    explainability = {
        "Age": round(_importance_for(bundle, "Age"), 4),
        "BMI": round(_importance_for(bundle, "BMI"), 4),
        "Smoking": round(_importance_for(bundle, "Smoking"), 4),
        "Disease": round(disease_importance, 4),
        "Number of Claims": round(_importance_for(bundle, "Number of Claims"), 4),
    }

    return {
        "criticality_score": predicted_score,
        "score_probabilities": {str(score): round(probability, 4) for score, probability in zip(class_labels, probabilities)},
        "explainability": explainability,
    }


def build_ai_insights(patients: list[dict[str, Any]]) -> dict[str, Any]:
    bundle = train_model(patients)

    feature_importance = {
        feature: round(importance, 4)
        for feature, importance in sorted(
            zip(bundle.feature_names, bundle.model.feature_importances_),
            key=lambda item: item[1],
            reverse=True,
        )
    }

    clusters = []
    for patient in patients:
        row = [_build_feature_vector(patient, bundle.feature_names)]
        probabilities = bundle.model.predict_proba(row)[0]
        class_labels = [int(label) for label in bundle.model.classes_]
        weighted_score = sum(score * probability for score, probability in zip(class_labels, probabilities))
        clusters.append(
            {
                "patient_name": patient.get("full_name", "Unknown"),
                "age": int(patient.get("age", 0) or 0),
                "claim_amount": _extract_claim_amount(patient),
                "predicted_risk": int(max(1, min(5, round(weighted_score)))),
            }
        )

    return {
        "feature_importance": feature_importance,
        "clustering_points": clusters,
    }


def _importance_for(bundle: ModelBundle, feature_name: str) -> float:
    for feature, importance in zip(bundle.feature_names, bundle.model.feature_importances_):
        if feature == feature_name:
            return float(importance)
    return 0.0