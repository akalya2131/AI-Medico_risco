import unittest

from risk_engine import calculate_risk


class RiskEngineTests(unittest.TestCase):
    def test_level_five_ckd_case_reaches_five(self):
        result = calculate_risk({
            "medical_history": ["CKD"],
            "claims": [{"diagnosis_codes": ["CKD"]}] * 4,
            "bmi": 32,
        })
        self.assertEqual(result["risk_score"], 5)
        self.assertTrue(result["claim_penalty_applied"])
        self.assertEqual(len(result["preventive_care_steps"]), 3)

    def test_level_four_copd_logic(self):
        result = calculate_risk({
            "medical_history": ["COPD", "Smoking"],
            "claims": [{"diagnosis_codes": ["COPD"]}],
        })
        self.assertEqual(result["risk_score"], 4)
        self.assertIn("copd", result["matched_conditions"])

    def test_diabetes_and_high_bmi_add_custom_step(self):
        result = calculate_risk({
            "medical_history": ["Type 2 Diabetes"],
            "claims": [{"diagnosis_codes": ["Diabetes"]}],
            "bmi": 33,
        })
        self.assertEqual(result["risk_score"], 4)
        self.assertIn("Suggest DASH Diet with structured weight-loss coaching", result["preventive_care_steps"])
        self.assertEqual(len(result["preventive_care_steps"]), 3)

    def test_stable_without_major_history(self):
        result = calculate_risk({"medical_history": [], "claims": []})
        self.assertEqual(result["risk_score"], 1)
        self.assertEqual(result["risk_label"], "Stable")


if __name__ == "__main__":
    unittest.main()
