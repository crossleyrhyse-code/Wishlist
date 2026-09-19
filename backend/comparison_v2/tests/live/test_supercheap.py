import argparse
from ...adapters.supercheap import search_supercheap,SupercheapUnavailable
from ...core.parser import parse_product
from ...core.matcher import compare_products
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("title"); ap.add_argument("--query"); ap.add_argument("--limit",type=int,default=20); a=ap.parse_args()
    q=a.query or a.title; tracked=parse_product(a.title)
    print("TRACKED :",a.title); print("SEARCH  :",q); print("-"*100)
    try: items=search_supercheap(q,a.limit)
    except SupercheapUnavailable as e: print("SUPERCHEAP AUTO UNAVAILABLE:",e); return
    rows=[]
    for x in items: rows.append((compare_products(tracked,parse_product(x.title)),x))
    rank={"EXACT":0,"SIMILAR":1,"POSSIBLE":2,"REJECT":3}
    rows.sort(key=lambda z:(rank.get(z[0].classification,9),-z[0].score,z[1].price is None,z[1].price or 0))
    counts={k:0 for k in rank}
    for i,(m,x) in enumerate(rows,1):
        counts[m.classification]=counts.get(m.classification,0)+1
        price=f"${x.price:.2f}" if x.price is not None else "price unavailable"
        print(f"{i:02}. {m.classification:<8} {m.score:>3}% | {price}"); print("   ",x.title); print("    reasons:",", ".join(m.reasons)); print("   ",x.url)
    print("-"*100); print(" | ".join(f"{k.lower()}={counts.get(k,0)}" for k in ("EXACT","SIMILAR","POSSIBLE","REJECT")))
if __name__=="__main__": main()
