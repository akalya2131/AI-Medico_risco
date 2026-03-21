import unittest

from app.services.patient_insights import build_analytics_summary, build_dashboard_stats, enrich_patients, get_high_risk_patients
from app.services.data import DEMO_HOSPITALS, DEMO_PATIENTS


class PatientInsightsTests(unittest.TestCase):
    def setUp(self):
        self.enriched_patients = enrich_patients(DEMO_PATIENTS, DEMO_HOSPITALS)

    def test_high_risk_patients_filtered_from_risk_score(self):
        high_risk = get_high_risk_patients(self.enriched_patients)
        self.assertTrue(high_risk)
        self.assertTrue(all(patient["risk"]["risk_score"] >= 4 for patient in high_risk))

    def test_dashboard_stats_count_high_risk_alerts(self):
        stats = build_dashboard_stats(self.enriched_patients)
        self.assertEqual(stats["high_risk_alerts"], len(get_high_risk_patients(self.enriched_patients)))
        self.assertGreater(stats["total_claims_inr"], 0)

    def test_analytics_summary_reports_diseases_and_risk_buckets(self):
        analytics = build_analytics_summary(self.enriched_patients)
        self.assertIn("diabetes", analytics["disease_counts"])
        self.assertIn("ckd", analytics["disease_counts"])
        self.assertEqual(set(analytics["risk_distribution"].keys()), {"1", "2", "3", "4", "5"})


if __name__ == "__main__":
    unittest.main()
