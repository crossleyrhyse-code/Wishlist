from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional

from ..adapters.bcf import BCFUnavailable, search_bcf
from ..adapters.bunnings import BunningsUnavailable, search_bunnings
from ..adapters.supercheap import SupercheapUnavailable, search_supercheap
from ..adapters.supacentre import SupacentreUnavailable, SupacentreNoResults, search_4wd_supacentre
from ..adapters.kickass import KickAssUnavailable, KickAssNoResults, search_kickass
from ..adapters.anaconda import AnacondaUnavailable, AnacondaNoResults, search_anaconda
from ..adapters.jbhifi import JBHiFiUnavailable, JBHiFiNoResults, search_jbhifi
from ..adapters.queueit import QueueItActive
from .matcher import compare_products
from .parser import parse_product
from .retailer_product import RetailerProduct

MATCH_ORDER = {"EXACT": 0, "SIMILAR": 1, "POSSIBLE": 2, "REJECT": 3}

@dataclass
class ComparisonCandidate:
    product: RetailerProduct
    classification: str
    score: int
    reasons: list[str] = field(default_factory=list)
    savings: Optional[float] = None

@dataclass
class RetailerStatus:
    retailer: str
    available: bool
    returned: int = 0
    error: Optional[str] = None
    status: str = "AVAILABLE"

@dataclass
class ComparisonRun:
    tracked_title: str
    tracked_price: Optional[float]
    query: str
    results: list[ComparisonCandidate]
    rejected: list[ComparisonCandidate]
    retailers: list[RetailerStatus]

RETAILERS: dict[str, tuple[Callable, object]] = {
    "Bunnings": (search_bunnings, BunningsUnavailable),
    "BCF": (search_bcf, BCFUnavailable),
    "Supercheap Auto": (search_supercheap, SupercheapUnavailable),
    "4WD Supacentre": (search_4wd_supacentre, (SupacentreUnavailable, SupacentreNoResults)),
    "KickAss Products": (search_kickass, (KickAssUnavailable, KickAssNoResults)),
    "Anaconda": (search_anaconda, (AnacondaUnavailable, AnacondaNoResults)),
    "JB Hi-Fi": (search_jbhifi, (JBHiFiUnavailable, JBHiFiNoResults)),
}

def _normalise_adapter_row(row):
    # Bunnings/BCF/Supercheap return RetailerProduct. 4WD and KickAss retain
    # useful structured metadata in dict rows. Normalise both forms here.
    if isinstance(row, RetailerProduct):
        return row, False
    if isinstance(row, dict):
        product = row.get("product")
        if isinstance(product, RetailerProduct):
            return product, bool(row.get("bundle"))
        title = str(row.get("title") or "").strip()
        url = str(row.get("url") or "").strip()
        if title and url:
            price = row.get("price")
            return RetailerProduct(
                retailer=str(row.get("retailer") or "Unknown"),
                title=title,
                url=url,
                price=price,
                price_text=f"${float(price):.2f}" if price is not None else None,
            ), bool(row.get("bundle"))
    raise TypeError(f"Unsupported retailer adapter row: {type(row).__name__}")

def _candidate_sort_key(c: ComparisonCandidate):
    # Match quality first. Within a class, priced results sort cheapest first;
    # unpriced results remain useful and come after priced products.
    return (
        MATCH_ORDER.get(c.classification, 99),
        1 if c.product.price is None else 0,
        c.product.price if c.product.price is not None else float("inf"),
        -c.score,
        c.product.retailer.lower(),
        c.product.title.lower(),
    )

def compare_across_retailers(
    tracked_title: str,
    *,
    tracked_price: Optional[float] = None,
    query: Optional[str] = None,
    retailers: Optional[list[str]] = None,
    limit_per_retailer: int = 20,
) -> ComparisonRun:
    tracked_title = str(tracked_title or "").strip()
    if not tracked_title:
        raise ValueError("tracked_title is required")
    search_query = str(query or tracked_title).strip()
    tracked = parse_product(tracked_title)
    wanted = retailers or list(RETAILERS)
    results, rejected, statuses = [], [], []

    for retailer in wanted:
        if retailer not in RETAILERS:
            statuses.append(RetailerStatus(retailer, False, error="Unsupported retailer."))
            continue
        searcher, unavailable_exc = RETAILERS[retailer]
        try:
            products = searcher(search_query, limit=limit_per_retailer)
            statuses.append(RetailerStatus(retailer, True, returned=len(products), status="AVAILABLE"))
        except QueueItActive as exc:
            statuses.append(RetailerStatus(
                retailer, False, error=str(exc), status="QUEUE_ACTIVE"
            ))
            continue
        except unavailable_exc as exc:
            statuses.append(RetailerStatus(retailer, False, error=str(exc)))
            continue
        except Exception as exc:
            # Retailer isolation: an unexpected adapter failure must not kill
            # comparison results from the other stores.
            statuses.append(RetailerStatus(retailer, False, error=f"{type(exc).__name__}: {exc}"))
            continue

        for row in products:
            product, force_bundle = _normalise_adapter_row(row)
            profile = parse_product(product.title)
            if force_bundle:
                profile.is_bundle = True
            match = compare_products(tracked, profile)
            savings = None
            if tracked_price is not None and product.price is not None:
                savings = round(float(tracked_price) - float(product.price), 2)
            item = ComparisonCandidate(
                product=product,
                classification=match.classification,
                score=match.score,
                reasons=list(match.reasons),
                savings=savings,
            )
            if match.classification == "REJECT":
                rejected.append(item)
            else:
                results.append(item)

    results.sort(key=_candidate_sort_key)
    rejected.sort(key=_candidate_sort_key)
    return ComparisonRun(tracked_title, tracked_price, search_query, results, rejected, statuses)
