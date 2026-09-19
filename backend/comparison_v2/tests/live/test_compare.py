from __future__ import annotations
import argparse
from ...core.engine import compare_across_retailers

def _money(v):
    return "price unavailable" if v is None else f"${v:.2f}"

def main():
    ap=argparse.ArgumentParser(description="Wishlist Comparison V2 multi-retailer harness")
    ap.add_argument("tracked_title")
    ap.add_argument("--price", type=float, default=None)
    ap.add_argument("--query", default=None)
    ap.add_argument("--limit", type=int, default=20)
    ap.add_argument("--retailers", nargs="+", choices=["Bunnings","BCF"], default=None)
    ap.add_argument("--show-rejected", action="store_true")
    args=ap.parse_args()

    run=compare_across_retailers(
        args.tracked_title, tracked_price=args.price, query=args.query,
        retailers=args.retailers, limit_per_retailer=args.limit
    )
    print(f"TRACKED : {run.tracked_title}")
    print(f"PRICE   : {_money(run.tracked_price)}")
    print(f"SEARCH  : {run.query}")
    print("-"*100)
    for s in run.retailers:
        if s.available:
            print(f"{s.retailer:<10}: OK ({s.returned} products)")
        else:
            print(f"{s.retailer:<10}: UNAVAILABLE ({s.error})")
    print("-"*100)

    if not run.results:
        print("NO COMPARABLE PRODUCTS FOUND")
    for i,c in enumerate(run.results,1):
        saving=""
        if c.savings is not None:
            saving=f" | {'SAVE' if c.savings>0 else 'OVER' if c.savings<0 else 'SAME'} ${abs(c.savings):.2f}"
        print(f"{i:02d}. {c.classification:<8} {c.score:>3}% | {c.product.retailer:<8} | {_money(c.product.price)}{saving}")
        print(f"    {c.product.title}")
        print(f"    reasons: {', '.join(c.reasons) if c.reasons else 'none'}")
        print(f"    {c.product.url}")

    if args.show_rejected and run.rejected:
        print("-"*100)
        print(f"REJECTED ({len(run.rejected)})")
        for c in run.rejected:
            print(f"    {c.product.retailer}: {c.product.title} | {', '.join(c.reasons) if c.reasons else 'none'}")
    print("-"*100)
    print(f"COMPARABLE: {len(run.results)} | REJECTED: {len(run.rejected)}")

if __name__=="__main__":
    main()
