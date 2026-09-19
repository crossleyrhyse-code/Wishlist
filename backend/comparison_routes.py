"""Compatibility API for the polished /compare UI, powered entirely by Comparison V2.

The frontend keeps its established response shape so the user-facing comparison
page does not need a visual redesign. All search, parsing, matching and pricing
comes from comparison_v2.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from comparison_v2.core.engine import RETAILERS, ComparisonCandidate, compare_across_retailers
from product_store import get_product_by_id

router = APIRouter(prefix="/compare", tags=["comparison"])


class ComparisonProduct(BaseModel):
    id: str
    name: Optional[str] = None
    displayName: Optional[str] = None
    store: str = ""
    category: Optional[str] = None
    url: str = ""
    targetPrice: Optional[float] = None
    imageUrl: Optional[str] = None
    currentPrice: Optional[float] = None
    productTitle: Optional[str] = None
    product_title: Optional[str] = None


class CompareRequest(BaseModel):
    selectedStores: List[str] = []
    product: Optional[ComparisonProduct] = None


class MoreMatchesRequest(BaseModel):
    product: Optional[ComparisonProduct] = None


def _product_snapshot(product_id: str, supplied: Optional[ComparisonProduct]):
    products, index = get_product_by_id(product_id)
    if products is not None and index is not None:
        return products[index]
    if supplied is not None and supplied.id == product_id:
        return supplied.model_dump()
    raise HTTPException(status_code=404, detail="Wishlist product was not found.")


def _comparison_title(product: dict) -> str:
    return str(
        product.get("productTitle")
        or product.get("product_title")
        or product.get("displayName")
        or product.get("name")
        or ""
    ).strip()


def _match_type(classification: str) -> str:
    return {
        "EXACT": "EXACT MATCH",
        "SIMILAR": "SIMILAR PRODUCT",
        "POSSIBLE": "POSSIBLE MATCH",
    }.get(classification, "NO MATCH")


def _serialize(candidate: ComparisonCandidate, current_price: Optional[float]):
    price = candidate.product.price
    price_difference = None
    saving = candidate.savings
    if price is not None and current_price is not None:
        price_difference = round(float(price) - float(current_price), 2)
        if saving is None:
            saving = round(float(current_price) - float(price), 2)

    # Keep the legacy numeric fields only for response compatibility. The UI now
    # displays V2 reasons rather than pretending these are separate V1 scores.
    return {
        "name": candidate.product.title,
        "url": candidate.product.url,
        "percentage": candidate.score,
        "nameScore": candidate.score,
        "identityScore": candidate.score,
        "numbersMatch": "model" in " ".join(candidate.reasons).lower(),
        "brandMatch": "brand" in " ".join(candidate.reasons).lower(),
        "reasons": list(candidate.reasons),
        "matchType": _match_type(candidate.classification),
        "price": price,
        "priceError": None,
        "priceDifference": price_difference,
        "saving": saving,
    }


def _retailer_payload(run, retailer: str, current_price: Optional[float], *, offset=0, page_size=5):
    status = next((item for item in run.retailers if item.retailer == retailer), None)
    candidates = [item for item in run.results if item.product.retailer == retailer]

    if status is None:
        return {
            "store": retailer,
            "searchedCount": 0,
            "strongestMatch": None,
            "matches": [],
            "hasMore": False,
            "nextOffset": 0,
            "reason": "UNAVAILABLE",
            "error": "Retailer status was unavailable.",
        }

    if not status.available:
        message = status.error or f"{retailer} is temporarily unavailable."
        if status.status == "QUEUE_ACTIVE":
            message = "Waiting room active. Try this retailer again shortly."
        return {
            "store": retailer,
            "searchedCount": status.returned,
            "strongestMatch": None,
            "matches": [],
            "hasMore": False,
            "nextOffset": 0,
            "reason": status.status,
            "error": message,
        }

    confident = [c for c in candidates if c.classification in {"EXACT", "SIMILAR"}]
    possible = [c for c in candidates if c.classification == "POSSIBLE"]

    if offset:
        page = candidates[offset: offset + page_size]
        return {
            "store": retailer,
            "matches": [_serialize(c, current_price) for c in page],
            "hasMore": offset + page_size < len(candidates),
            "nextOffset": offset + len(page),
        }

    visible = candidates[:page_size]
    strongest = confident[0] if confident else None
    reason = None
    if strongest is None:
        reason = "POSSIBLE_ONLY" if possible else "NO_MATCH"

    return {
        "store": retailer,
        "searchedCount": status.returned,
        "strongestMatch": _serialize(strongest, current_price) if strongest else None,
        "matches": [_serialize(c, current_price) for c in visible],
        "hasMore": len(candidates) > page_size,
        "nextOffset": len(visible),
        "reason": reason,
        "error": None,
    }


@router.get("/supported-stores")
def get_supported_stores():
    # This is now the single source of truth for the sidebar/developer page too.
    # Kmart is intentionally absent until a production adapter exists.
    return {"success": True, "stores": list(RETAILERS.keys())}


@router.get("/stores")
def get_available_comparison_stores():
    return {"success": True, "stores": list(RETAILERS.keys())}


@router.post("/{product_id}")
def compare_product(product_id: str, request: CompareRequest):
    product = _product_snapshot(product_id, request.product)
    title = _comparison_title(product)
    if not title:
        raise HTTPException(status_code=400, detail="This product does not have a usable comparison title.")

    selected = request.selectedStores or list(RETAILERS.keys())
    unknown = [store for store in selected if store not in RETAILERS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unsupported retailer(s): {', '.join(unknown)}")

    current_price = product.get("currentPrice")
    run = compare_across_retailers(
        title,
        tracked_price=current_price,
        retailers=selected,
        limit_per_retailer=20,
    )

    retailers = [
        _retailer_payload(run, store, current_price, page_size=5)
        for store in selected
    ]

    return {
        "success": True,
        "product": {
            "id": product_id,
            "name": product.get("name") or product.get("displayName") or title,
            "comparisonTitle": title,
            "store": product.get("store") or "",
            "url": product.get("url") or "",
            "imageUrl": product.get("imageUrl"),
            "currentPrice": current_price,
            "targetPrice": product.get("targetPrice"),
        },
        "selectedStores": selected,
        "retailers": retailers,
    }


@router.post("/{product_id}/more/{store}")
def more_matches(
    product_id: str,
    store: str,
    request: MoreMatchesRequest,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=5, ge=1, le=10),
):
    if store not in RETAILERS:
        raise HTTPException(status_code=400, detail=f"Unsupported retailer: {store}")

    product = _product_snapshot(product_id, request.product)
    title = _comparison_title(product)
    current_price = product.get("currentPrice")

    # Re-run only this retailer. This keeps the V2 engine as the single matching
    # implementation while preserving the polished UI's "5 more" interaction.
    run = compare_across_retailers(
        title,
        tracked_price=current_price,
        retailers=[store],
        limit_per_retailer=min(50, max(20, offset + limit)),
    )
    payload = _retailer_payload(
        run,
        store,
        current_price,
        offset=offset,
        page_size=limit,
    )
    return {
        "success": True,
        "store": store,
        "matches": payload["matches"],
        "hasMore": payload["hasMore"],
        "nextOffset": payload["nextOffset"],
    }
