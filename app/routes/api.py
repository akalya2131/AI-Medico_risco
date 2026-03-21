from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from app.services.ai_patient_analysis import analyze_patient_input, build_patient_payload, derive_ai_analysis_from_patient
from app.services.patient_insights import build_analytics_summary, build_dashboard_stats, enrich_patients, get_high_risk_patients
from app.services.supabase_service import HealthcareRepository
from app.utils.geo import closest_hospital
from ml_engine import build_ai_insights, predict_patient_risk
from risk_engine import calculate_risk

api_bp = Blueprint("api", __name__)


def get_repository() -> HealthcareRepository:
    return HealthcareRepository(current_app.config)


def api_login_required():
    if not session.get("user"):
        return jsonify({"error": "Authentication required."}), 401
    return None


def api_role_required(*allowed_roles: str):
    auth_error = api_login_required()
    if auth_error:
        return auth_error
    if session.get("user", {}).get("role") not in allowed_roles:
        return jsonify({"error": "Forbidden for current role."}), 403
    return None


def build_dashboard_payload(repo: HealthcareRepository) -> dict:
    enriched_patients = enrich_patients(repo.list_patients(), repo.list_hospitals())
    return {
        "patients": enriched_patients,
        "high_risk_patients": get_high_risk_patients(enriched_patients),
        "stats": build_dashboard_stats(enriched_patients),
        "analytics": build_analytics_summary(enriched_patients),
        "ai_insights": build_ai_insights(enriched_patients),
    }


@api_bp.route("/predict", methods=["POST"])
def predict():
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    repo = get_repository()
    patient_id = payload.get("patient_id")

    patient = repo.get_patient(patient_id) if patient_id else payload
    if patient is None:
        return jsonify({"error": "Patient not found."}), 404

    prediction = calculate_risk(patient)
    nearest = closest_hospital(patient, repo.list_hospitals()) if prediction["risk_score"] >= 4 else None
    return jsonify({**prediction, "closest_hospital": nearest})


@api_bp.route("/patients/<patient_id>", methods=["GET"])
def patient_detail(patient_id: str):
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    repo = get_repository()
    patient = repo.get_patient(patient_id)
    if patient is None:
        return jsonify({"error": "Patient not found."}), 404

    prediction = calculate_risk(patient)
    nearest = closest_hospital(patient, repo.list_hospitals()) if prediction["risk_score"] >= 4 else None
    return jsonify({**patient, "risk": prediction, "closest_hospital": nearest})


@api_bp.route("/high-risk", methods=["GET"])
def high_risk_patients():
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    repo = get_repository()
    patients = enrich_patients(repo.list_patients(), repo.list_hospitals())
    high_risk = get_high_risk_patients(patients)
    return jsonify({"count": len(high_risk), "patients": high_risk})


@api_bp.route("/analytics", methods=["GET"])
def analytics():
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    repo = get_repository()
    patients = enrich_patients(repo.list_patients(), repo.list_hospitals())
    return jsonify(build_analytics_summary(patients))


@api_bp.route("/ai-analysis-preview", methods=["POST"])
def ai_analysis_preview():
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    return jsonify(analyze_patient_input(payload))


@api_bp.route("/patients/analyze", methods=["POST"])
def create_analyzed_patient():
    auth_error = api_role_required("admin")
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    patient_payload = build_patient_payload(payload)

    repo = get_repository()
    training_patients = repo.list_patients()
    ml_prediction = predict_patient_risk(patient_payload, training_patients)
    patient_payload["ml_criticality_score"] = ml_prediction["criticality_score"]
    patient_payload["ml_explainability"] = ml_prediction["explainability"]
    patient_payload["risk_score"] = ml_prediction["criticality_score"]
    patient_payload["risk_label"] = f"Risk {ml_prediction['criticality_score']}"

    created_patient = repo.create_patient(patient_payload)
    enriched_patient = {
        **created_patient,
        "risk": calculate_risk(created_patient),
        "ai_analysis": created_patient.get("ai_analysis") or derive_ai_analysis_from_patient(created_patient),
        "ml_prediction": ml_prediction,
    }
    dashboard_payload = build_dashboard_payload(repo)
    return jsonify({"success": True, "patient": enriched_patient, "dashboard": dashboard_payload}), 201


@api_bp.route("/simulator", methods=["POST"])
def simulator():
    auth_error = api_login_required()
    if auth_error:
        return auth_error

    payload = request.get_json(silent=True) or {}
    patient_data = {
        "age": payload.get("age"),
        "bmi": payload.get("bmi"),
        "medical_history": payload.get("medical_history", []),
        "claims": payload.get("claims", []),
        "diagnosis_codes": payload.get("diagnosis_codes", []),
    }
    prediction = calculate_risk(patient_data)
    return jsonify(prediction)