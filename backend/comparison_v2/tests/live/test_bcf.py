from __future__ import annotations

import argparse

from ...adapters.bcf import BCFUnavailable, search_bcf
from ...core.matcher import compare_products
from ...core.parser import parse_product

ORDER = {"EXACT": 0, "SIMILAR": 1, "POSSIBLE": 2, "REJECT": 3}


def main():
    ap = argparse.ArgumentParser(description="Standalone Wishlist Comparison V2 BCF test harness")
    ap.add_argument("tracked_title")
    ap.add_argument("--query", default=None)
    ap.add_argument("--limit", type=int, default=20)
    args = ap.parse_args()

    query = args.query or args.tracked_title
    tracked = parse_product(args.tracked_title)

    print(f"TRACKED : {args.tracked_title}")
    print(f"SEARCH  : {query}")
    print("-" * 90)

    try:
        products = search_bcf(query, limit=args.limit)
    except BCFUnavailable as e:
        print(f"BCF UNAVAILABLE: {e}")
        return

    rows = []
    for p in products:
        profile = parse_product(p.title)
        match = compare_products(tracked, profile)
        rows.append((match, p, profile))

    rows.sort(key=lambda r: (ORDER.get(r[0].classification, 99), -r[0].score, r[1].title.lower()))
    counts = {"EXACT": 0, "SIMILAR": 0, "POSSIBLE": 0, "REJECT": 0}

    for i, (match, p, profile) in enumerate(rows, 1):
        counts[match.classification] = counts.get(match.classification, 0) + 1
        price = p.price_text or "price unavailable"
        print(f"{i:02d}. {match.classification:<8} {match.score:>3}% | {price}")
        print(f"    {p.title}")
        print(f"    parsed: type={profile.product_type} brand={profile.brand} model={profile.model} voltage={profile.voltage}")
        print(f"    reasons: {', '.join(match.reasons) if match.reasons else 'none'}")
        print(f"    {p.url}")

    print("-" * 90)
    print(
        f"RESULTS: {len(rows)} | exact={counts['EXACT']} | similar={counts['SIMILAR']} | "
        f"possible={counts['POSSIBLE']} | rejected={counts['REJECT']}"
    )


if __name__ == "__main__":
    main()
