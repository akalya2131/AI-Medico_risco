from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for

from app.services.supabase_service import HealthcareRepository
from app.utils.geo import closest_hospital
from risk_engine import calculate_risk

web_bp = Blueprint("web", __name__)


def get_repository() -> HealthcareRepository:
    return HealthcareRepository(current_app.config)


def login_required(view):
    from functools import wraps

    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            flash("Please sign in to access the command center.", "error")
            return redirect(url_for("web.login"))
        return view(*args, **kwargs)

    return wrapped


@web_bp.route("/")
def index():
    if session.get("user"):
        return redirect(url_for("web.dashboard"))
    return redirect(url_for("web.login"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        repo = get_repository()
        session["user"] = repo.authenticate_user(
            email=request.form.get("email", "doctor@command.center"),
            password=request.form.get("password", ""),
        )
        flash("Signed in to the AI healthcare command center.", "success")
        return redirect(url_for("web.dashboard"))
    return render_template("login.html")


@web_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        repo = get_repository()
        session["user"] = repo.register_user(
            full_name=request.form.get("full_name", "Dr. Command Center"),
            email=request.form.get("email", "doctor@command.center"),
            password=request.form.get("password", ""),
        )
        flash("Workspace created. You are now in the command center.", "success")
        return redirect(url_for("web.dashboard"))
    return render_template("register.html")


@web_bp.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("web.login"))


@web_bp.route("/dashboard")
@login_required
def dashboard():
    repo = get_repository()
    enriched_patients = enrich_patients(repo.list_patients(), repo.list_hospitals())
    stats = build_dashboard_stats(enriched_patients)
    return render_template(
        "dashboard.html",
        patients=enriched_patients,
        hospitals=repo.list_hospitals(),
        supabase_ready=repo.is_configured,
        stats=stats,
    )


@web_bp.route("/add-patient", methods=["GET", "POST"])
@login_required
def add_patient():
    if request.method == "POST":
        diagnosis = request.form.get("primary_diagnosis", "").strip()
        patient_payload = {
            "full_name": request.form.get("full_name", "").strip(),
            "age": int(request.form.get("age", 0) or 0),
            "gender": request.form.get("gender", ""),
            "city": request.form.get("city", "").strip(),
            "primary_diagnosis": diagnosis,
            "medical_history": [diagnosis] if diagnosis else [],
            "claims": [],
            "timeline": [],
            "documents": [],
            "lat": 20.5937,
            "lng": 78.9629,
            "bmi": None,
        }
        initial_risk = calculate_risk(patient_payload)
        patient_payload["risk_score"] = initial_risk["risk_score"]
        patient_payload["risk_label"] = initial_risk["risk_label"]
        patient_payload["preventive_care_steps"] = initial_risk["preventive_care_steps"]

        repo = get_repository()
        patient = repo.create_patient(patient_payload)
        flash("Patient created and initial risk calculated.", "success")
        return redirect(url_for("web.detail_page", patient_id=patient["id"]))

    return render_template("add_patient.html")


@web_bp.route("/patients/<patient_id>")
@login_required
def detail_page(patient_id: str):
    repo = get_repository()
    patient = repo.get_patient(patient_id)
    if patient is None:
        flash("Patient record was not found.", "error")
        return redirect(url_for("web.dashboard"))

    hospitals = repo.list_hospitals()
    risk = calculate_risk(patient)
    nearest = closest_hospital(patient, hospitals) if risk["risk_score"] >= 4 else None
    patient_context = {**patient, "risk": risk, "closest_hospital": nearest}
    return render_template("detail.html", patient=patient_context, hospitals=hospitals)


@web_bp.route("/patients/<patient_id>/history", methods=["POST"])
@login_required
def add_history_record(patient_id: str):
    history_payload = {
        "title": request.form.get("title", "Treatment update").strip(),
        "date": request.form.get("date", "").strip(),
        "detail": request.form.get("detail", "").strip(),
    }
    repo = get_repository()
    repo.add_history_record(patient_id, history_payload)
    flash("Medical history record added.", "success")
    return redirect(url_for("web.detail_page", patient_id=patient_id) + "#history")


@web_bp.route("/patients/<patient_id>/claims", methods=["POST"])
@login_required
def add_claim_record(patient_id: str):
    diagnosis_codes = [item.strip() for item in request.form.get("diagnosis_codes", "").split(",") if item.strip()]
    claim_payload = {
        "claim_id": request.form.get("claim_id", f"CLM-{uuid4().hex[:6].upper()}"),
        "provider": request.form.get("provider", "").strip(),
        "amount_inr": float(request.form.get("amount_inr", 0) or 0),
        "status": request.form.get("status", "").strip(),
        "diagnosis_codes": diagnosis_codes,
        "date": request.form.get("date", "").strip(),
    }
    repo = get_repository()
    repo.add_claim_record(patient_id, claim_payload)
    flash("Insurance claim record added.", "success")
    return redirect(url_for("web.detail_page", patient_id=patient_id) + "#claims")


@web_bp.route("/patients/<patient_id>/documents", methods=["POST"])
@login_required
def upload_document(patient_id: str):
    report = request.files.get("document")
    if not report or not report.filename:
        flash("Choose a PDF or report file before uploading.", "error")
        return redirect(url_for("web.detail_page", patient_id=patient_id))

    repo = get_repository()
    repo.upload_document(patient_id, report)
    flash("Document added to the vault.", "success")
    return redirect(url_for("web.detail_page", patient_id=patient_id) + "#vault")


@web_bp.route("/patients/<patient_id>/documents/<path:storage_key>/delete", methods=["POST"])
@login_required
def delete_document(patient_id: str, storage_key: str):
    repo = get_repository()
    deleted = repo.delete_document(patient_id, storage_key)
    flash("Document removed from the vault." if deleted else "Unable to remove document.", "success" if deleted else "error")
    return redirect(url_for("web.detail_page", patient_id=patient_id) + "#vault")


@web_bp.route("/uploads/<path:filename>")
@login_required
def uploaded_file(filename: str):
    upload_folder = Path(current_app.config["UPLOAD_FOLDER"])
    return send_from_directory(upload_folder, filename)


def enrich_patients(patients: list[dict], hospitals: list[dict]) -> list[dict]:
    enriched_patients = []
    for patient in patients:
        prediction = calculate_risk(patient)
        nearest = closest_hospital(patient, hospitals) if prediction["risk_score"] >= 4 else None
        enriched_patients.append({**patient, "risk": prediction, "closest_hospital": nearest})
    return enriched_patients


def build_dashboard_stats(patients: list[dict]) -> dict:
    total_patients = len(patients)
    total_risk = sum(patient["risk"]["risk_score"] for patient in patients)
    average_risk = round(total_risk / total_patients, 1) if total_patients else 0
    total_claims_inr = 0
    high_risk_alerts = 0
    risk_distribution = {"Stable": 0, "Low": 0, "Moderate": 0, "High": 0, "Critical": 0}
    claims_trend: dict[str, float] = defaultdict(float)

    for patient in patients:
        risk_distribution[patient["risk"]["risk_label"]] += 1
        if patient["risk"]["risk_score"] >= 4:
            high_risk_alerts += 1
        for claim in patient.get("claims", []):
            total_claims_inr += float(claim.get("amount_inr", 0) or 0)
            claims_trend[str(claim.get("date", "Unknown"))[:7]] += float(claim.get("amount_inr", 0) or 0)

    ordered_trend = [{"month": month, "amount_inr": round(amount, 2)} for month, amount in sorted(claims_trend.items())]
    return {
        "total_patients": total_patients,
        "average_risk": average_risk,
        "total_claims_inr": round(total_claims_inr, 2),
        "high_risk_alerts": high_risk_alerts,
        "risk_distribution": risk_distribution,
        "claims_trend": ordered_trend,
    }
