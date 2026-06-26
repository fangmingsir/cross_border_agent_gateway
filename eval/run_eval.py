from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.agent import analyze_sku
from app.schemas import AnalyzeSkuRequest


def main() -> None:
    cases = json.loads((ROOT / "eval" / "eval_cases.json").read_text(encoding="utf-8"))
    rows = []
    for case in cases:
        response = analyze_sku(
            AnalyzeSkuRequest(
                sku=case["sku"],
                marketplace=case["marketplace"],
                question=case["question"],
                operator_role="operator",
            )
        )
        called_tools = [result.name for result in response.tool_results]
        evidence_ok = all(response.evidence.get(key) is not None for key in case["expected_evidence"])
        tool_ok = all(tool in called_tools for tool in case["expected_tools"])
        review_ok = response.human_review_required == case["expected_review"]
        rows.append(
            {
                "id": case["id"],
                "status": response.status,
                "tool_ok": tool_ok,
                "evidence_ok": evidence_ok,
                "review_ok": review_ok,
                "risk_level": response.risk_level,
                "estimated_cost_usd": response.cost.estimated_cost_usd,
            }
        )

    print(json.dumps(rows, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
