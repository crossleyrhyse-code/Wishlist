import argparse
from ...adapters.supacentre import search_4wd_supacentre_multi,SupacentreUnavailable
from ...core.parser import parse_product
from ...core.matcher import compare_products

SCENARIOS=[
 ("Kings Plus 270° Tourer XL Freestanding Awning MKII","270 awning"),
 ("Kings Plus 270° Tourer XL Freestanding Awning MKII","awning"),
 ("Kings 2x3m Side Awning","side awning"),
]

def run(title,query,limit):
    print("="*118); print("TRACKED:",title); print("SEED QUERY:",query)
    tracked=parse_product(title)
    try: rows,diag=search_4wd_supacentre_multi(query,limit=limit)
    except SupacentreUnavailable as e: print("UNAVAILABLE:",e); return
    print("DISCOVERY:", " | ".join(f"{q}={status}:{n}" for q,status,n in diag))
    ranked=[]
    for row in rows:
        p=row["product"]; profile=parse_product(p.title)
        if row["bundle"]: profile.is_bundle=True
        ranked.append((compare_products(tracked,profile),row))
    order={"EXACT":0,"SIMILAR":1,"POSSIBLE":2,"REJECT":3}
    ranked.sort(key=lambda x:(order.get(x[0].classification,9),-x[0].score,x[1]["product"].price is None,x[1]["product"].price or 0))
    counts={k:0 for k in order}
    for i,(m,row) in enumerate(ranked,1):
        p=row["product"]; counts[m.classification]+=1
        print(f"{i:02}. {m.classification:<8} {m.score:>3}% | {p.price_text or 'price unavailable':>17} | bundle={row['bundle']}")
        print("   ",p.title); print("   ",p.url)
    print("COUNTS:", " | ".join(f"{k.lower()}={counts[k]}" for k in order))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=20)
    a=ap.parse_args()
    print("G1.5.3 4WD SUPACENTRE MULTI-QUERY DISCOVERY / LIVE REGRESSION")
    for title,q in SCENARIOS: run(title,q,a.limit)
if __name__=="__main__": main()
