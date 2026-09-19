from __future__ import annotations
from fastapi import APIRouter, HTTPException

from .api_models import (
    CompareV2Request, CompareV2Response, CompareV2ResultResponse,
    RetailerStatusResponse,
)
from .core.engine import RETAILERS, compare_across_retailers

router = APIRouter(tags=["Comparison V2"])

@router.post("/compare-v2", response_model=CompareV2Response)
def compare_v2(request: CompareV2Request):
    if request.retailers:
        unknown=[r for r in request.retailers if r not in RETAILERS]
        if unknown:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported retailer(s): {', '.join(unknown)}"
            )
    try:
        run=compare_across_retailers(
            request.title,
            tracked_price=request.price,
            query=request.query,
            retailers=request.retailers,
            limit_per_retailer=request.limit_per_retailer,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    return CompareV2Response(
        tracked_title=run.tracked_title,
        tracked_price=run.tracked_price,
        query=run.query,
        retailers=[
            RetailerStatusResponse(
                retailer=s.retailer, available=s.available,
                returned=s.returned, error=s.error, status=s.status
            ) for s in run.retailers
        ],
        results=[
            CompareV2ResultResponse(
                retailer=c.product.retailer,
                title=c.product.title,
                url=c.product.url,
                price=c.product.price,
                price_text=c.product.price_text,
                classification=c.classification,
                score=c.score,
                reasons=c.reasons,
                savings=c.savings,
            ) for c in run.results
        ],
        rejected_count=len(run.rejected),
    )
