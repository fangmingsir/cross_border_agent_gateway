from __future__ import annotations

import argparse
import json

from .agent import analyze_sku
from .schemas import AnalyzeSkuRequest


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ecommerce Agent gateway demo offline.")
    parser.add_argument("--sku", default="SKU-USB-C-001")
    parser.add_argument("--marketplace", default="US")
    parser.add_argument("--question", default="这个 SKU 在美国站转化差，帮我分析并给出调价和 listing 优化建议")
    parser.add_argument("--operator-role", default="operator")
    args = parser.parse_args()

    response = analyze_sku(
        AnalyzeSkuRequest(
            sku=args.sku,
            marketplace=args.marketplace,
            question=args.question,
            operator_role=args.operator_role,
        )
    )
    print(json.dumps(response.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

