from __future__ import annotations

from functools import lru_cache

from .data_store import find_one
from .schemas import ToolResult


@lru_cache(maxsize=128)
def query_product_catalog(sku: str, marketplace: str) -> ToolResult:
    row = find_one("products.json", sku, marketplace)
    if not row:
        return ToolResult("query_product_catalog", False, error="PRODUCT_NOT_FOUND")
    return ToolResult("query_product_catalog", True, data=row)


@lru_cache(maxsize=128)
def query_order_stats(sku: str, marketplace: str) -> ToolResult:
    row = find_one("orders.json", sku, marketplace)
    if not row:
        return ToolResult("query_order_stats", False, error="ORDER_STATS_NOT_FOUND")
    return ToolResult("query_order_stats", True, data=row)


@lru_cache(maxsize=128)
def query_refund_risk(sku: str, marketplace: str) -> ToolResult:
    row = find_one("refunds.json", sku, marketplace)
    if not row:
        return ToolResult("query_refund_risk", False, error="REFUND_RISK_NOT_FOUND")
    return ToolResult("query_refund_risk", True, data=row)


@lru_cache(maxsize=128)
def estimate_margin(sku: str, marketplace: str) -> ToolResult:
    row = find_one("margins.json", sku, marketplace)
    if not row:
        return ToolResult("estimate_margin", False, error="MARGIN_NOT_FOUND")

    revenue = float(row["avg_sale_price"])
    total_cost = float(row["landed_cost"]) + float(row["platform_fee"]) + float(row["ad_cost_per_unit"])
    margin = revenue - total_cost
    margin_rate = margin / revenue if revenue else 0.0
    data = dict(row)
    data.update({"unit_margin": round(margin, 2), "margin_rate": round(margin_rate, 4)})
    return ToolResult("estimate_margin", True, data=data)


def generate_listing_suggestions(product: dict, orders: dict, refunds: dict, margin: dict) -> ToolResult:
    suggestions: list[str] = []
    conversion_rate = float(orders.get("conversion_rate", 0))
    refund_rate = float(refunds.get("refund_rate", 0))
    margin_rate = float(margin.get("margin_rate", 0))
    rating = float(product.get("rating", 0))

    if conversion_rate < 0.08:
        suggestions.append("优化主图与标题前 80 字，突出核心卖点和适配场景。")
    if rating < 4.3:
        suggestions.append("优先处理差评关键词，补充尺码、材质、安装方式等说明。")
    if refund_rate > 0.08:
        suggestions.append("在详情页前半屏补充退货高频原因，降低误购。")
    if margin_rate > 0.25 and conversion_rate < 0.08:
        suggestions.append("保留利润空间，先做小幅 coupon 或广告词优化，不直接大幅降价。")
    if margin_rate < 0.15:
        suggestions.append("暂停主动降价，先排查物流、平台费和广告 ACOS。")

    if not suggestions:
        suggestions.append("当前指标无明显异常，建议继续观察 7 天并按广告词维度拆分。")

    return ToolResult("generate_listing_suggestions", True, data={"suggestions": suggestions})


def cache_info() -> dict[str, int]:
    infos = [
        query_product_catalog.cache_info(),
        query_order_stats.cache_info(),
        query_refund_risk.cache_info(),
        estimate_margin.cache_info(),
    ]
    return {
        "hits": sum(info.hits for info in infos),
        "misses": sum(info.misses for info in infos),
        "currsize": sum(info.currsize for info in infos),
    }

