from __future__ import annotations

from functools import wraps
from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, send_from_directory, session, url_for

from app.services.ai_patient_analysis import build_patient_payload, derive_ai_analysis_from_patient
from app.services.patient_insights import build_analytics_summary, build_dashboard_stats, enrich_patients, get_high_risk_patients
from app.services.supabase_service import HealthcareRepository
from app.utils.geo import closest_hospital
from risk_engine import calculate_risk

web_bp = Blueprint("web", __name__)


def get_repository() -> HealthcareRepository:
    return HealthcareRepository(current_app.config)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("user"):
            flash("Please sign in to access the command center.", "error")
            return redirect(url_for("web.login"))
        return view(*args, **kwargs)

    return wrapped


def role_required(*allowed_roles: str):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            user = session.get("user")
            if not user:
                flash("Please sign in to access the command center.", "error")
                return redirect(url_for("web.login"))
            if user.get("role") not in allowed_roles:
                flash("Your role does not have access to that action.", "error")
                return redirect(url_for("web.dashboard"))
            return view(*args, **kwargs)

        return wrapped

    return decorator


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
            full_name=request.form.get("full_name", ""),
            email=request.form.get("email", "doctor@command.center"),
            password=request.form.get("password", ""),
            role=request.form.get("role", "doctor"),
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
            role=request.form.get("role", "doctor"),
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
    analytics = build_analytics_summary(enriched_patients)
    high_risk_patients = get_high_risk_patients(enriched_patients)
    return render_template(
        "dashboard.html",
        patients=enriched_patients,
        high_risk_patients=high_risk_patients,
        hospitals=repo.list_hospitals(),
        supabase_ready=repo.is_configured,
        stats=stats,
        analytics=analytics,
        current_user=session.get("user", {}),
    )


@web_bp.route("/add-patient", methods=["GET", "POST"])
@role_required("admin")
def add_patient():
    if request.method == "POST":
        patient_payload = build_patient_payload(
            {
                "patient_name": request.form.get("patient_name", "").strip(),
                "age": request.form.get("age", 0),
                "gender": request.form.get("gender", ""),
                "city": request.form.get("city", "Care Hub"),
                "bmi": request.form.get("bmi", 0),
                "smoking_status": request.form.get("smoking_status", "No"),
                "disease": request.form.get("disease", "Diabetes"),
                "claim_amount": request.form.get("claim_amount", 0),
                "claim_frequency": request.form.get("claim_frequency", 0),
            }
        )
        repo = get_repository()
        patient = repo.create_patient(patient_payload)
        flash("Patient created and AI analysis completed.", "success")
        return redirect(url_for("web.detail_page", patient_id=patient["id"], new_patient="1") + "#overview")

    return render_template("add_patient.html", current_user=session.get("user", {}))


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
    patient_context = {
        **patient,
        "risk": risk,
        "closest_hospital": nearest,
        "is_high_risk": risk["risk_score"] >= 4,
        "ai_analysis": patient.get("ai_analysis") or derive_ai_analysis_from_patient(patient),
    }
    return render_template(
        "detail.html",
        patient=patient_context,
        hospitals=hospitals,
        current_user=session.get("user", {}),
        new_patient_created=request.args.get("new_patient") == "1",
    )


@web_bp.route("/patients/<patient_id>/history", methods=["POST"])
@role_required("admin")
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
@role_required("admin")
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
@role_required("admin")
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
@role_required("admin")
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
