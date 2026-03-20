from __future__ import annotations

from pathlib import Path
from typing import Any
from uuid import uuid4

try:
    from supabase import create_client
except ImportError:  # pragma: no cover
    create_client = None


class SupabaseStorageHelper:
    def __init__(self, config: dict[str, Any]):
        self.upload_root = Path(config["UPLOAD_FOLDER"])
        self.upload_root.mkdir(exist_ok=True)
        self.bucket_name = config.get("SUPABASE_BUCKET", "medical-reports")
        self._client = self._build_client(config)

    @staticmethod
    def _build_client(config: dict[str, Any]):
        url = config.get("SUPABASE_URL")
        key = config.get("SUPABASE_SERVICE_ROLE_KEY") or config.get("SUPABASE_KEY")
        if not url or not key or create_client is None:
            return None
        try:
            return create_client(url, key)
        except Exception:
            return None

    @property
    def is_configured(self) -> bool:
        return self._client is not None

    def save_patient_report(self, patient_id: str, uploaded_file) -> dict[str, str]:
        safe_name = uploaded_file.filename.replace(" ", "_")
        storage_key = f"{patient_id}/{uuid4().hex}_{safe_name}"
        destination = self.upload_root / storage_key
        destination.parent.mkdir(parents=True, exist_ok=True)
        uploaded_file.save(destination)

        document = {
            "title": uploaded_file.filename,
            "storage_key": storage_key,
            "url": f"/uploads/{storage_key}",
            "type": destination.suffix.lower().replace(".", "") or "file",
        }

        if self._client:
            try:
                with destination.open("rb") as file_handle:
                    self._client.storage.from_(self.bucket_name).upload(storage_key, file_handle.read())
                document["url"] = self._client.storage.from_(self.bucket_name).get_public_url(storage_key)
            except Exception:
                pass

        return document

    def delete_patient_report(self, storage_key: str) -> bool:
        deleted = False
        if self._client:
            try:
                self._client.storage.from_(self.bucket_name).remove([storage_key])
                deleted = True
            except Exception:
                deleted = False

        local_path = self.upload_root / storage_key
        if local_path.exists():
            local_path.unlink()
            deleted = True
        return deleted
