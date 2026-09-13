from typing import List

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from comparison import (
    get_live_retailer_price,
    score_search_results,
    search_bcf,
    search_bunnings,
)
from price_checker import get_product_title
from product_store import get_product_by_id, save_products
from store_manager import get_store_names


router = APIRouter(prefix="/compare", tags=["comparison"])


class CompareRequest(BaseModel):
    selectedStores: List[str] = []


RETAILER_SEARCHERS = {
    "BCF": search_bcf,
    "Bunnings": search_bunnings,
}


def _get_saved_product(product_id: str):
    products, product_index = get_product_by_id(product_id)

    if products is None or product_index is None:
        raise HTTPException(
            status_code=404,
            detail="Wishlist product was not found.",
        )

    return products, product_index, products[product_index]


def _get_comparison_title(product: dict):
    saved_title = (
        product.get("productTitle")
        or product.get("product_title")
        or ""
    ).strip()

    if saved_title:
        return saved_title

    product_url = (product.get("url") or "").strip()

    if not product_url:
        return (
            product.get("displayName")
            or product.get("name")
            or "Unknown product"
        )

    try:
        title = get_product_title({"url": product_url}).strip()
    except Exception:
        title = (
            product.get("displayName")
            or product.get("name")
            or "Unknown product"
        )

    return title


def _serialize_candidate(candidate: dict, current_price=None):
    live_price = candidate.get("price")

    saving = None
    price_difference = None

    if live_price is not None and current_price is not None:
        price_difference = round(float(live_price) - float(current_price), 2)
        saving = round(float(current_price) - float(live_price), 2)

    return {
        "name": candidate.get("name"),
        "url": candidate.get("url"),
        "percentage": candidate.get("percentage"),
        "nameScore": candidate.get("name_score"),
        "identityScore": candidate.get("identity_score"),
        "numbersMatch": candidate.get("numbers_match"),
        "brandMatch": candidate.get("brand_match"),
        "matchType": candidate.get("match_type"),
        "price": live_price,
        "priceError": candidate.get("price_error"),
        "priceDifference": price_difference,
        "saving": saving,
    }


def _price_candidates(store_name: str, candidates: list, current_price=None):
    priced = []

    for candidate in candidates:
        item = dict(candidate)
        item["price"] = None
        item["price_error"] = None

        try:
            item["price"] = get_live_retailer_price(
                store_name,
                candidate,
            )
        except Exception as error:
            item["price_error"] = str(error)

        priced.append(
            _serialize_candidate(
                item,
                current_price=current_price,
            )
        )

    return priced


def _search_and_score(store_name: str, comparison_title: str):
    search_function = RETAILER_SEARCHERS.get(store_name)

    if search_function is None:
        raise HTTPException(
            status_code=400,
            detail=f"{store_name} is not a supported comparison store.",
        )

    raw_results = search_function(comparison_title)

    return score_search_results(
        comparison_title,
        raw_results,
    )


def _has_confident_match(scored_results: list):
    return any(
        result.get("match_type") in {"EXACT MATCH", "SIMILAR PRODUCT"}
        for result in scored_results
    )


def _has_possible_match(scored_results: list):
    return any(
        result.get("match_type") == "POSSIBLE MATCH"
        for result in scored_results
    )


@router.get("/supported-stores")
def get_supported_stores():
    """
    Return every retailer currently supported by Wishlist.

    This list comes directly from store_manager.py so the frontend
    does not need to maintain its own duplicate store list.
    """
    return {
        "success": True,
        "stores": get_store_names(),
    }


@router.get("/stores")
def get_available_comparison_stores():
    return {
        "success": True,
        "stores": list(RETAILER_SEARCHERS.keys()),
    }


@router.post("/{product_id}")
def compare_product(product_id: str, request: CompareRequest):
    products, product_index, product = _get_saved_product(product_id)

    comparison_title = _get_comparison_title(product)

    if comparison_title and not (
        product.get("productTitle") or product.get("product_title")
    ):
        product["productTitle"] = comparison_title
        products[product_index] = product
        save_products(products)

    current_price = product.get("currentPrice")
    current_store = (product.get("store") or "").strip()

    requested_stores = [
        store
        for store in request.selectedStores
        if store in RETAILER_SEARCHERS and store.lower() != current_store.lower()
    ]

    retailers = []

    for store_name in requested_stores:
        try:
            scored_results = _search_and_score(
                store_name,
                comparison_title,
            )

            confident_match_exists = _has_confident_match(scored_results)
            possible_match_exists = _has_possible_match(scored_results)

            if not confident_match_exists and not possible_match_exists:
                retailers.append(
                    {
                        "store": store_name,
                        "searchedCount": len(scored_results),
                        "strongestMatch": None,
                        "matches": [],
                        "hasMore": False,
                        "nextOffset": 0,
                        "reason": "NO_MATCH",
                    }
                )
                continue

            if confident_match_exists:
                # Main match + three other matches
                initial_slice = scored_results[:4]
                reason = None
            else:
                # Do not promote a possible match as the main retailer result.
                # Show up to three possible matches for user inspection.
                possible_results = [
                    result
                    for result in scored_results
                    if result.get("match_type") == "POSSIBLE MATCH"
                ]
                initial_slice = possible_results[:3]
                reason = "POSSIBLE_ONLY"

            priced_matches = _price_candidates(
                store_name,
                initial_slice,
                current_price=current_price,
            )

            source_count = (
                len(scored_results)
                if confident_match_exists
                else len([
                    result
                    for result in scored_results
                    if result.get("match_type") == "POSSIBLE MATCH"
                ])
            )

            retailers.append(
                {
                    "store": store_name,
                    "searchedCount": len(scored_results),
                    "strongestMatch": (
                        priced_matches[0]
                        if confident_match_exists and priced_matches
                        else None
                    ),
                    "matches": priced_matches,
                    "hasMore": source_count > len(initial_slice),
                    "nextOffset": len(initial_slice),
                    "reason": reason,
                }
            )

        except Exception as error:
            retailers.append(
                {
                    "store": store_name,
                    "searchedCount": 0,
                    "strongestMatch": None,
                    "matches": [],
                    "hasMore": False,
                    "nextOffset": 0,
                    "error": str(error),
                }
            )

    return {
        "success": True,
        "product": {
            "id": product.get("id"),
            "name": product.get("displayName") or product.get("name"),
            "comparisonTitle": comparison_title,
            "store": product.get("store"),
            "url": product.get("url"),
            "imageUrl": product.get("imageUrl"),
            "currentPrice": current_price,
            "targetPrice": product.get("targetPrice"),
        },
        "selectedStores": requested_stores,
        "retailers": retailers,
    }


@router.post("/{product_id}/more/{store_name}")
def load_more_matches(
    product_id: str,
    store_name: str,
    offset: int = Query(default=4, ge=0),
    limit: int = Query(default=5, ge=1, le=10),
):
    _, _, product = _get_saved_product(product_id)

    if store_name not in RETAILER_SEARCHERS:
        raise HTTPException(
            status_code=400,
            detail=f"{store_name} is not a supported comparison store.",
        )

    if (product.get("store") or "").strip().lower() == store_name.lower():
        raise HTTPException(
            status_code=400,
            detail="The selected retailer is already the tracked store.",
        )

    comparison_title = _get_comparison_title(product)
    current_price = product.get("currentPrice")

    scored_results = _search_and_score(
        store_name,
        comparison_title,
    )

    confident_match_exists = _has_confident_match(scored_results)
    possible_match_exists = _has_possible_match(scored_results)

    if not confident_match_exists and not possible_match_exists:
        return {
            "success": True,
            "store": store_name,
            "matches": [],
            "hasMore": False,
            "nextOffset": offset,
            "reason": "NO_MATCH",
        }

    if confident_match_exists:
        source_results = scored_results
    else:
        source_results = [
            result
            for result in scored_results
            if result.get("match_type") == "POSSIBLE MATCH"
        ]

    next_slice = source_results[offset : offset + limit]

    priced_matches = _price_candidates(
        store_name,
        next_slice,
        current_price=current_price,
    )

    next_offset = offset + len(next_slice)

    return {
        "success": True,
        "store": store_name,
        "matches": priced_matches,
        "hasMore": next_offset < len(source_results),
        "nextOffset": next_offset,
    }
