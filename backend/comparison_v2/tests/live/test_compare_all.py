import argparse
from ...core.engine import compare_across_retailers, RETAILERS
def main():
    p=argparse.ArgumentParser()
    p.add_argument("title"); p.add_argument("--price",type=float); p.add_argument("--query"); p.add_argument("--limit",type=int,default=20)
    a=p.parse_args()
    print("COMPARISON V2 - MULTI-RETAILER LIVE TEST")
    print("RETAILERS:", ", ".join(RETAILERS))
    r=compare_across_retailers(a.title,tracked_price=a.price,query=a.query,limit_per_retailer=a.limit)
    print("\nRETAILER STATUS")
    for s in r.retailers:
        print(f"- {s.retailer}: {s.status} | returned={s.returned}" + (f" | {s.error}" if s.error else ""))
    print("\nCOMPARABLE RESULTS")
    for i,c in enumerate(r.results,1):
        price="PRICE UNAVAILABLE" if c.product.price is None else f"${c.product.price:.2f}"
        print(f"{i:02}. {c.classification:<8} {c.score:>3}% | {c.product.retailer:<18} | {price}")
        print("   ",c.product.title)
    print(f"\nSUMMARY: comparable={len(r.results)} | rejected={len(r.rejected)}")
if __name__=="__main__": main()
