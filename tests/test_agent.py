import unittest

from app.agent import analyze_sku
from app.schemas import AnalyzeSkuRequest


class AgentTest(unittest.TestCase):
    def test_low_conversion_sku_returns_structured_evidence(self):
        response = analyze_sku(
            AnalyzeSkuRequest(
                sku="SKU-USB-C-001",
                marketplace="US",
                question="这个 SKU 在美国站转化差，帮我分析并给出调价和 listing 优化建议",
            )
        )

        self.assertEqual(response.status, "ok")
        self.assertEqual(response.evidence["conversion_rate"], 0.05)
        self.assertEqual(response.evidence["refund_rate"], 0.095)
        self.assertTrue(response.recommendations)
        self.assertIn("generate_listing_suggestions", [result.name for result in response.tool_results])

    def test_unknown_sku_falls_back_without_hallucinated_evidence(self):
        response = analyze_sku(
            AnalyzeSkuRequest(
                sku="SKU-NOT-FOUND",
                marketplace="US",
                question="帮我诊断这个 SKU",
            )
        )

        self.assertEqual(response.status, "fallback")
        self.assertTrue(response.human_review_required)
        self.assertEqual(response.evidence, {})
        self.assertIn("商品基础信息", response.missing_evidence)


if __name__ == "__main__":
    unittest.main()
