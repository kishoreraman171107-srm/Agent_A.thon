import unittest
from engine.protocol_rules import parse_protocol

class ProtocolRuleTests(unittest.TestCase):
    def test_version_two(self):
        rules = parse_protocol('Version 2. Visit window: plus or minus 3 days. Creatinine > 1.5 mg/dL')
        self.assertEqual(rules.version, 2)
        self.assertEqual(rules.visit_window_days, 3)
        self.assertEqual(rules.creatinine_exclusion_mg_dl, 1.5)

    def test_version_three_medications(self):
        rules = parse_protocol('Version 3. Prohibited: Sulfonylurea and Systemic Glucocorticoid')
        self.assertIn('sulfonylurea', rules.prohibited_medications)
        self.assertIn('systemic glucocorticoid', rules.prohibited_medications)

if __name__ == '__main__':
    unittest.main()
