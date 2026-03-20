from __future__ import annotations

DEMO_HOSPITALS = [
    {"id": "aiims-delhi", "name": "AIIMS Delhi", "city": "New Delhi", "specialty": "Nephrology & Cardiology", "lat": 28.5672, "lng": 77.2100},
    {"id": "apollo-chennai", "name": "Apollo Hospitals Chennai", "city": "Chennai", "specialty": "Cardiac Sciences", "lat": 13.0632, "lng": 80.2518},
    {"id": "fortis-bengaluru", "name": "Fortis Bengaluru", "city": "Bengaluru", "specialty": "Pulmonology & Critical Care", "lat": 12.9346, "lng": 77.6146},
    {"id": "medanta-gurugram", "name": "Medanta Gurugram", "city": "Gurugram", "specialty": "Multi-Specialty Tertiary Care", "lat": 28.4397, "lng": 77.0405},
]

DEMO_PATIENTS = [
    {
        "id": "pt-001", "full_name": "Aarav Mehta", "age": 67, "gender": "Male", "city": "New Delhi", "lat": 28.6139, "lng": 77.2090,
        "bmi": 29.4, "member_id": "IND-4401", "primary_diagnosis": "CKD", "medical_history": ["CKD", "Hypertension", "Smoking"],
        "claims": [
            {"claim_id": "CLM-9001", "provider": "Niva Bupa", "amount_inr": 185000, "status": "Approved", "diagnosis_codes": ["CKD"], "date": "2025-09-18"},
            {"claim_id": "CLM-9002", "provider": "Niva Bupa", "amount_inr": 124000, "status": "Approved", "diagnosis_codes": ["Hypertension"], "date": "2025-10-22"},
            {"claim_id": "CLM-9003", "provider": "Niva Bupa", "amount_inr": 148000, "status": "Settled", "diagnosis_codes": ["CKD"], "date": "2026-01-06"},
            {"claim_id": "CLM-9004", "provider": "Niva Bupa", "amount_inr": 201000, "status": "Under Review", "diagnosis_codes": ["Heart Failure"], "date": "2026-02-11"},
        ],
        "documents": [
            {"title": "Renal Function Report.pdf", "url": "/uploads/pt-001/renal-function-report.pdf", "type": "pdf", "storage_key": "pt-001/renal-function-report.pdf"},
            {"title": "Cardiology Summary.pdf", "url": "/uploads/pt-001/cardiology-summary.pdf", "type": "pdf", "storage_key": "pt-001/cardiology-summary.pdf"},
        ],
        "timeline": [
            {"title": "Admitted for fluid overload", "date": "2026-02-11", "detail": "Managed in cardiac ICU for acute decompensation at Medanta."},
            {"title": "Nephrology consult", "date": "2026-01-07", "detail": "Stage 3 CKD monitoring plan updated at AIIMS Delhi."},
            {"title": "Cardiology review", "date": "2025-10-23", "detail": "Heart failure screening follow-up with medication optimization."},
        ],
    },
    {
        "id": "pt-002", "full_name": "Diya Iyer", "age": 52, "gender": "Female", "city": "Chennai", "lat": 13.0827, "lng": 80.2707,
        "bmi": 31.8, "member_id": "IND-4402", "primary_diagnosis": "Diabetes", "medical_history": ["Type 2 Diabetes", "Asthma"],
        "claims": [
            {"claim_id": "CLM-9201", "provider": "Star Health", "amount_inr": 76000, "status": "Approved", "diagnosis_codes": ["Diabetes"], "date": "2025-08-03"},
            {"claim_id": "CLM-9202", "provider": "Star Health", "amount_inr": 42000, "status": "Approved", "diagnosis_codes": ["Asthma"], "date": "2025-12-14"},
        ],
        "documents": [{"title": "HbA1c Panel.pdf", "url": "/uploads/pt-002/hba1c-panel.pdf", "type": "pdf", "storage_key": "pt-002/hba1c-panel.pdf"}],
        "timeline": [
            {"title": "Diabetes review", "date": "2025-08-05", "detail": "Quarterly HbA1c check completed at Apollo Chennai."},
            {"title": "Pulmonology follow-up", "date": "2025-12-16", "detail": "Asthma inhaler plan refreshed after urgent visit."},
        ],
    },
    {
        "id": "pt-003", "full_name": "Kabir Singh", "age": 43, "gender": "Male", "city": "Bengaluru", "lat": 12.9716, "lng": 77.5946,
        "bmi": 27.2, "member_id": "IND-4403", "primary_diagnosis": "COPD", "medical_history": ["COPD", "Smoking"],
        "claims": [
            {"claim_id": "CLM-9301", "provider": "HDFC Ergo", "amount_inr": 64000, "status": "Approved", "diagnosis_codes": ["COPD"], "date": "2025-11-04"},
            {"claim_id": "CLM-9302", "provider": "HDFC Ergo", "amount_inr": 38000, "status": "Settled", "diagnosis_codes": ["Respiratory Infection"], "date": "2026-01-12"},
        ],
        "documents": [{"title": "Pulmonary Function Test.pdf", "url": "/uploads/pt-003/pulmonary-function-test.pdf", "type": "pdf", "storage_key": "pt-003/pulmonary-function-test.pdf"}],
        "timeline": [
            {"title": "Pulmonology escalation", "date": "2026-01-12", "detail": "Frequent respiratory claims triggered specialist review at Fortis Bengaluru."},
            {"title": "Smoking cessation counselling", "date": "2025-11-06", "detail": "Respiratory care team initiated cessation pathway."},
        ],
    },
    {
        "id": "pt-004", "full_name": "Meera Nair", "age": 34, "gender": "Female", "city": "Mumbai", "lat": 19.0760, "lng": 72.8777,
        "bmi": 23.6, "member_id": "IND-4404", "primary_diagnosis": "Allergies", "medical_history": ["Allergies"],
        "claims": [{"claim_id": "CLM-9401", "provider": "ICICI Lombard", "amount_inr": 12000, "status": "Approved", "diagnosis_codes": ["Allergies"], "date": "2026-02-28"}],
        "documents": [{"title": "Allergy Panel.pdf", "url": "/uploads/pt-004/allergy-panel.pdf", "type": "pdf", "storage_key": "pt-004/allergy-panel.pdf"}],
        "timeline": [{"title": "Routine allergy review", "date": "2026-02-28", "detail": "Seasonal trigger mapping updated with Mumbai care team."}],
    },
]
