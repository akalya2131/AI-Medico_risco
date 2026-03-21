import unittest

from app.services.ai_patient_analysis import analyze_patient_input, build_patient_payload, derive_ai_analysis_from_patient


class AIPatientAnalysisTests(unittest.TestCase):
    def test_analyze_patient_input_returns_high_risk_for_severe_profile(self):
        analysis = analyze_patient_input(
            {
                "age": 68,
                "bmi": 33,
                "smoking_status": "Yes",
                "disease": "Heart Disease",
                "claim_amount": 250000,
                "claim_frequency": 5,
            }
        )
        self.assertGreaterEqual(analysis["risk_score"], 71)
        self.assertEqual(analysis["risk_level"], "High")
        self.assertTrue(analysis["insights"])
        self.assertTrue(analysis["recommendations"])

    def test_build_patient_payload_creates_claims_and_ai_analysis(self):
        payload = build_patient_payload(
            {
                "patient_name": "Test Patient",
                "age": 45,
                "gender": "Female",
                "city": "Delhi",
                "bmi": 28.5,
                "smoking_status": "No",
                "disease": "Diabetes",
                "claim_amount": 55000,
                "claim_frequency": 2,
            }
        )
        self.assertEqual(payload["full_name"], "Test Patient")
        self.assertEqual(len(payload["claims"]), 2)
        self.assertIn("ai_analysis", payload)
        self.assertEqual(payload["ai_analysis"]["risk_level"], "Medium")

    def test_derive_ai_analysis_from_existing_patient(self):
        patient = {
            "age": 39,
            "bmi": 24,
            "primary_diagnosis": "Asthma",
            "medical_history": ["Asthma"],
            "claims": [{"amount_inr": 12000}],
        }
        analysis = derive_ai_analysis_from_patient(patient)
        self.assertIn(analysis["risk_level"], {"Low", "Medium", "High"})
        self.assertEqual(len(analysis["contributions"]), 6)


if __name__ == "__main__":
    unittest.main()
