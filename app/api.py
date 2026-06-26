from __future__ import annotations

from fastapi import FastAPI
from pydantic import BaseModel, Field

from .agent import analyze_sku
from .schemas import AnalyzeSkuRequest


app = FastAPI(
    title="Cross-border Ecommerce Agent Gateway",
    version="0.1.0",
    description="Interview-ready Agent gateway demo with tool use, fallback, tracing, and cost logging.",
)


class AnalyzeSkuPayload(BaseModel):
    sku: str = Field(..., examples=["SKU-USB-C-001"])
    marketplace: str = Field(..., examples=["US"])
    question: str = Field(..., examples=["这个 SKU 在美国站转化差，帮我分析并给出调价和 listing 优化建议"])
    operator_role: str = Field("operator", examples=["operator"])


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/agent/analyze-sku")
def analyze(payload: AnalyzeSkuPayload) -> dict:
    request = AnalyzeSkuRequest(
        sku=payload.sku,
        marketplace=payload.marketplace,
        question=payload.question,
        operator_role=payload.operator_role,
    )
    return analyze_sku(request).to_dict()

