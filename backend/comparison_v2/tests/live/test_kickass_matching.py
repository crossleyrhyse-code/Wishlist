import argparse
from ...adapters.kickass import search_kickass, KickAssUnavailable, KickAssNoResults
from ...core.parser import parse_product
from ...core.matcher import compare_products

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("tracked",nargs="?",default="KickAss Pocket Blower")
    ap.add_argument("--query",default="pocket blower")
    ap.add_argument("--limit",type=int,default=20)
    a=ap.parse_args()
    print("H1.3 KICKASS LIVE MATCHING DIAGNOSTIC")
    print("TRACKED:",a.tracked); print("QUERY:",a.query)
    tracked=parse_product(a.tracked)
    try: rows=search_kickass(a.query,a.limit)
    except KickAssNoResults as e: print("NO RESULTS:",e); return
    except KickAssUnavailable as e: print("UNAVAILABLE:",e); return
    counts={"EXACT":0,"SIMILAR":0,"POSSIBLE":0,"REJECT":0}
    for i,x in enumerate(rows,1):
        cand=parse_product(x["title"])
        if x["bundle"]:
            cand.is_bundle=True
        m=compare_products(tracked,cand)
        counts[m.classification]=counts.get(m.classification,0)+1
        p="PRICE UNAVAILABLE" if x["price"] is None else f'${x["price"]:.2f}'
        print(f'{i:02}. {m.classification:<8} {m.score:>3}% | {p:>18} | bundle={x["bundle"]} | type={cand.product_type}')
        print("   ",x["title"]); print("   ",x["url"])
        if m.reasons: print("    REASON:","; ".join(m.reasons))
    print("COUNTS:"," | ".join(f"{k.lower()}={counts.get(k,0)}" for k in ("EXACT","SIMILAR","POSSIBLE","REJECT")))
    print(f'HEALTH: returned={len(rows)} | priced={sum(x["price"] is not None for x in rows)} | bundles={sum(x["bundle"] for x in rows)}')
if __name__=="__main__":main()
