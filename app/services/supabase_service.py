from __future__ import annotations

from copy import deepcopy
from typing import Any
from uuid import uuid4

from app.services.data import DEMO_HOSPITALS, DEMO_PATIENTS
from supabase_helper import SupabaseStorageHelper

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None


class HealthcareRepository:
    def __init__(self, app_config: dict[str, Any]):
        self.storage = SupabaseStorageHelper(app_config)
        self._supabase = self._build_client(app_config)

    @staticmethod
    def _build_client(app_config: dict[str, Any]):
        url = app_config.get("SUPABASE_URL")
        key = app_config.get("SUPABASE_SERVICE_ROLE_KEY") or app_config.get("SUPABASE_KEY")
        if not url or not key or create_client is None:
            return None
        try:
            return create_client(url, key)
        except Exception:
            return None

    @property
    def is_configured(self) -> bool:
        return self._supabase is not None

    def authenticate_user(self, email: str, password: str) -> dict[str, str]:
        if self._supabase:
            try:
                self._supabase.auth.sign_in_with_password({"email": email, "password": password})
            except Exception:
                pass
        return {"email": email, "full_name": email.split("@")[0].replace(".", " ").title()}

    def register_user(self, full_name: str, email: str, password: str) -> dict[str, str]:
        if self._supabase:
            try:
                self._supabase.auth.sign_up({"email": email, "password": password})
            except Exception:
                pass
        return {"email": email, "full_name": full_name or email.split("@")[0].replace(".", " ").title()}

    def list_patients(self) -> list[dict[str, Any]]:
        if not self._supabase:
            return deepcopy(DEMO_PATIENTS)
        response = self._supabase.table("patients").select("*, claims(*), documents(*), medical_history_entries(*)").execute()
        patients = response.data or []
        for patient in patients:
            patient.setdefault("timeline", patient.get("medical_history_entries", []))
            patient.setdefault("claims", patient.get("claims", []))
            patient.setdefault("documents", patient.get("documents", []))
        return patients

    def get_patient(self, patient_id: str) -> dict[str, Any] | None:
        patients = self.list_patients()
        for patient in patients:
            if str(patient.get("id")) == str(patient_id):
                return deepcopy(patient)
        return None

    def list_hospitals(self) -> list[dict[str, Any]]:
        return deepcopy(DEMO_HOSPITALS)

    def create_patient(self, patient_payload: dict[str, Any]) -> dict[str, Any]:
        patient_record = {**patient_payload}
        if self._supabase:
            try:
                response = self._supabase.table("patients").insert(patient_record).execute()
                return response.data[0] if response.data else patient_record
            except Exception:
                pass

        patient_record.setdefault("id", f"pt-{uuid4().hex[:6]}")
        patient_record.setdefault("member_id", f"IND-{uuid4().hex[:4].upper()}")
        patient_record.setdefault("claims", [])
        patient_record.setdefault("timeline", [])
        patient_record.setdefault("documents", [])
        DEMO_PATIENTS.append(patient_record)
        return patient_record

    def add_history_record(self, patient_id: str, history_payload: dict[str, Any]) -> dict[str, Any]:
        if self._supabase:
            try:
                response = self._supabase.table("medical_history_entries").insert({**history_payload, "patient_id": patient_id}).execute()
                return response.data[0] if response.data else history_payload
            except Exception:
                pass

        for patient in DEMO_PATIENTS:
            if str(patient.get("id")) == str(patient_id):
                patient.setdefault("timeline", []).append(history_payload)
                return history_payload
        return history_payload

    def add_claim_record(self, patient_id: str, claim_payload: dict[str, Any]) -> dict[str, Any]:
        if self._supabase:
            try:
                response = self._supabase.table("claims").insert({**claim_payload, "patient_id": patient_id}).execute()
                return response.data[0] if response.data else claim_payload
            except Exception:
                pass

        for patient in DEMO_PATIENTS:
            if str(patient.get("id")) == str(patient_id):
                patient.setdefault("claims", []).append(claim_payload)
                return claim_payload
        return claim_payload

    def upload_document(self, patient_id: str, uploaded_file) -> dict[str, Any]:
        document = self.storage.save_patient_report(patient_id, uploaded_file)
        if not self._supabase:
            for patient in DEMO_PATIENTS:
                if str(patient.get("id")) == str(patient_id):
                    patient.setdefault("documents", []).append(document)
                    break
        return document

    def delete_document(self, patient_id: str, storage_key: str) -> bool:
        deleted = self.storage.delete_patient_report(storage_key)
        for patient in DEMO_PATIENTS:
            if str(patient.get("id")) == str(patient_id):
                patient["documents"] = [doc for doc in patient.get("documents", []) if doc.get("storage_key") != storage_key]
                break
        return deleted
