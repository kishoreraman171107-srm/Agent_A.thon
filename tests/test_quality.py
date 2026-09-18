import unittest

from engine.quality import evidence_ref, validate_tables


class QualityTests(unittest.TestCase):
    def test_evidence_reference_uses_domain_subject_sequence(self):
        row = {"USUBJID": "X-S01-001", "LBSEQ": "4"}
        self.assertEqual(evidence_ref("LB", row, 1), "LB|X-S01-001|4")

    def test_missing_keys_are_reported(self):
        result = validate_tables({"DM": [{"USUBJID": ""}]})
        self.assertFalse(result["valid"])
        self.assertGreaterEqual(result["issue_count"], 1)

    def test_valid_row(self):
        result = validate_tables({"DM": [{"USUBJID": "X-S01-001", "DMSEQ": "1"}]})
        self.assertTrue(result["valid"])


if __name__ == "__main__":
    unittest.main()
