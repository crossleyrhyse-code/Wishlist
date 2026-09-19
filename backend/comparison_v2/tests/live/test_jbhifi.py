import argparse
from ...adapters.jbhifi import search_jbhifi, JBHiFiUnavailable, JBHiFiNoResults
from ...core.parser import parse_product
from ...core.matcher import compare_products

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("query", nargs="?", default="Ring video doorbell")
    ap.add_argument("--tracked", default="Ring Battery Video Doorbell 2K (Speckled Grey)")
    ap.add_argument("--limit", type=int, default=20)
    a=ap.parse_args()
    print("JB HI-FI LIVE ADAPTER")
    print("QUERY:", a.query)
    print("TRACKED:", a.tracked)
    try:
        rows=search_jbhifi(a.query, limit=a.limit)
    except JBHiFiNoResults as e:
        print("NO RESULTS:", e); return
    except JBHiFiUnavailable as e:
        print("UNAVAILABLE:", e); return
    tracked=parse_product(a.tracked)
    for i,row in enumerate(rows,1):
        p=row["product"]
        m=compare_products(tracked,parse_product(p.title))
        price="PRICE UNAVAILABLE" if p.price is None else f"${p.price:.2f}"
        print(f"{i:02}. {m.classification:<8} {m.score:>3}% | {price:>18} | SKU={row['sku'] or '-'}")
        print("   ",p.title)
        print("   ",p.url)
    print(f"HEALTH: returned={len(rows)} | priced={sum(r['product'].price is not None for r in rows)}")
if __name__=="__main__": main()
