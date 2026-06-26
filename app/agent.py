from __future__ import annotations

from .schemas import AgentTraceEvent, AnalyzeSkuRequest, AnalyzeSkuResponse, CostLog, ToolResult
from .tools import (
    cache_info,
    estimate_margin,
    generate_listing_suggestions,
    query_order_stats,
    query_product_catalog,
    query_refund_risk,
)


REQUIRED_TOOLS = {
    "query_product_catalog": "商品基础信息",
    "query_order_stats": "订单与转化数据",
    "query_refund_risk": "退款风险数据",
    "estimate_margin": "利润估算数据",
}


def analyze_sku(request: AnalyzeSkuRequest) -> AnalyzeSkuResponse:
    trace = [
        AgentTraceEvent("request_received", f"{request.marketplace}:{request.sku} by {request.operator_role}"),
        AgentTraceEvent("planner", "Planner selected product, order, refund, margin, and listing suggestion tools."),
    ]

    before_cache = cache_info()
    tool_results: list[ToolResult] = [
        query_product_catalog(request.sku, request.marketplace),
        query_order_stats(request.sku, request.marketplace),
        query_refund_risk(request.sku, request.marketplace),
        estimate_margin(request.sku, request.marketplace),
    ]

    result_by_name = {result.name: result for result in tool_results}
    missing = [
        label
        for tool_name, label in REQUIRED_TOOLS.items()
        if not result_by_name[tool_name].ok
    ]

    if not result_by_name["query_product_catalog"].ok:
        summary = "未找到商品基础信息，无法给出可靠运营建议。"
        return _build_response(request, "fallback", summary, {}, [], "unknown", True, missing, tool_results, trace)

    product = result_by_name["query_product_catalog"].data
    orders = result_by_name["query_order_stats"].data if result_by_name["query_order_stats"].ok else {}
    refunds = result_by_name["query_refund_risk"].data if result_by_name["query_refund_risk"].ok else {}
    margin = result_by_name["estimate_margin"].data if result_by_name["estimate_margin"].ok else {}

    suggestion_result = generate_listing_suggestions(product, orders, refunds, margin)
    tool_results.append(suggestion_result)

    evidence = {
        "title": product.get("title"),
        "category": product.get("category"),
        "rating": product.get("rating"),
        "sessions_7d": orders.get("sessions_7d"),
        "orders_7d": orders.get("orders_7d"),
        "conversion_rate": orders.get("conversion_rate"),
        "refund_rate": refunds.get("refund_rate"),
        "top_refund_reason": refunds.get("top_reason"),
        "unit_margin": margin.get("unit_margin"),
        "margin_rate": margin.get("margin_rate"),
    }

    risk_level = _risk_level(evidence, missing)
    human_review_required = risk_level == "high" or bool(missing)
    status = "partial" if missing else "ok"
    trace.append(AgentTraceEvent("guardrail", f"risk_level={risk_level}, human_review_required={human_review_required}"))
    trace.append(AgentTraceEvent("cost_control", "Used compact prompt, cached tool reads, and structured evidence only."))

    summary = _summary(request, evidence, missing)
    recommendations = suggestion_result.data["suggestions"]
    after_cache = cache_info()
    cost = _estimate_cost(request, len(tool_results), after_cache["hits"] - before_cache["hits"])

    return AnalyzeSkuResponse(
        sku=request.sku.upper(),
        marketplace=request.marketplace.upper(),
        status=status,
        summary=summary,
        evidence=evidence,
        recommendations=recommendations,
        risk_level=risk_level,
        human_review_required=human_review_required,
        missing_evidence=missing,
        tool_results=tool_results,
        trace=trace,
        cost=cost,
    )


def _summary(request: AnalyzeSkuRequest, evidence: dict, missing: list[str]) -> str:
    conversion_rate = evidence.get("conversion_rate")
    refund_rate = evidence.get("refund_rate")
    margin_rate = evidence.get("margin_rate")

    parts = [f"{request.marketplace.upper()} 站点 {request.sku.upper()} 的运营诊断已完成"]
    if conversion_rate is not None:
        parts.append(f"转化率 {conversion_rate:.1%}")
    if refund_rate is not None:
        parts.append(f"退款率 {refund_rate:.1%}")
    if margin_rate is not None:
        parts.append(f"毛利率 {margin_rate:.1%}")
    if missing:
        parts.append("但缺少 " + "、".join(missing))
    return "，".join(parts) + "。"


def _risk_level(evidence: dict, missing: list[str]) -> str:
    if missing:
        return "high"
    refund_rate = float(evidence.get("refund_rate") or 0)
    margin_rate = float(evidence.get("margin_rate") or 0)
    conversion_rate = float(evidence.get("conversion_rate") or 0)
    if refund_rate > 0.12 or margin_rate < 0.12:
        return "high"
    if refund_rate > 0.08 or conversion_rate < 0.06:
        return "medium"
    return "low"


def _estimate_cost(request: AnalyzeSkuRequest, tool_calls: int, cache_hits: int) -> CostLog:
    prompt_tokens = 120 + len(request.question.split()) * 2
    completion_tokens = 220
    estimated_cost = (prompt_tokens * 0.00000015) + (completion_tokens * 0.0000006)
    return CostLog(
        prompt_tokens_estimate=prompt_tokens,
        completion_tokens_estimate=completion_tokens,
        tool_calls=tool_calls,
        cache_hits=cache_hits,
        estimated_cost_usd=round(estimated_cost, 6),
    )


def _build_response(
    request: AnalyzeSkuRequest,
    status: str,
    summary: str,
    evidence: dict,
    recommendations: list[str],
    risk_level: str,
    human_review_required: bool,
    missing: list[str],
    tool_results: list[ToolResult],
    trace: list[AgentTraceEvent],
) -> AnalyzeSkuResponse:
    trace.append(AgentTraceEvent("fallback", "Stopped generation because required product evidence was missing."))
    return AnalyzeSkuResponse(
        sku=request.sku.upper(),
        marketplace=request.marketplace.upper(),
        status=status,
        summary=summary,
        evidence=evidence,
        recommendations=recommendations,
        risk_level=risk_level,
        human_review_required=human_review_required,
        missing_evidence=missing,
        tool_results=tool_results,
        trace=trace,
        cost=_estimate_cost(request, len(tool_results), 0),
    )

