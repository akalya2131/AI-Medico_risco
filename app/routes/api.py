from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request, session

from app.services.supabase_service import HealthcareRepository
from app.utils.geo import closest_hospital
from risk_engine import calculate_risk

api_bp = Blueprint("api", __name__)


def get_repository() -> HealthcareRepository:
    return HealthcareRepository(current_app.config)


def api_login_required():
    if not session.get("user"):
        return jsonify({"error": "Authentication required."}), 401
    return None


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
