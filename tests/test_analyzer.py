import unittest

from mergeguard.analyzer import _complexity_spike, _security_sensitive, _risk_tier, _gate


class AnalyzerHeuristicTests(unittest.TestCase):
    def test_complexity_spike_with_large_file(self) -> None:
        text = "\n".join(["line"] * 300)
        self.assertTrue(_complexity_spike(text, changed_lines=50))

    def test_complexity_spike_with_small_file(self) -> None:
        text = "\n".join(["line"] * 50)
        self.assertFalse(_complexity_spike(text, changed_lines=20))

    def test_security_sensitive_detects_keywords(self) -> None:
        self.assertTrue(_security_sensitive("src/auth_service.ts", "normal code"))
        self.assertTrue(_security_sensitive("src/worker.ts", "token validation flow"))

    def test_security_sensitive_ignores_normal_file(self) -> None:
        self.assertFalse(_security_sensitive("src/math.ts", "pure add function"))

    def test_risk_tier_boundaries(self) -> None:
        self.assertEqual(_risk_tier(85), "Low")
        self.assertEqual(_risk_tier(70), "Medium")
        self.assertEqual(_risk_tier(30), "High")

    def test_gate_boundaries(self) -> None:
        self.assertEqual(_gate(80), "Pass")
        self.assertEqual(_gate(65), "Review required")
        self.assertEqual(_gate(40), "Block")


if __name__ == "__main__":
    unittest.main()
