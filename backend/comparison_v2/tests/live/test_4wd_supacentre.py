import argparse
from ...adapters.supacentre import search_4wd_supacentre,SupacentreUnavailable
from ...core.parser import parse_product
from ...core.matcher import compare_products

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("title")
    ap.add_argument("--query")
    ap.add_argument("--limit",type=int,default=20)
    a=ap.parse_args()
    tracked=parse_product(a.title); q=a.query or a.title
    print("G1.5 4WD SUPACENTRE STANDALONE ADAPTER")
    print("TRACKED:",a.title); print("SEARCH :",q); print("-"*110)
    try: rows=search_4wd_supacentre(q,a.limit)
    except SupacentreUnavailable as e: print("4WD SUPACENTRE UNAVAILABLE:",e); return
    print(f"RETURNED: {len(rows)} usable/sample records after category filtering and bundle-aware selection")
    ranked=[]
    for row in rows:
        p=row["product"]
        profile=parse_product(p.title)
        if row["bundle"]:
            profile.is_bundle=True
        m=compare_products(tracked,profile)
        ranked.append((m,row))
    order={"EXACT":0,"SIMILAR":1,"POSSIBLE":2,"REJECT":3}
    ranked.sort(key=lambda x:(order.get(x[0].classification,9),-x[0].score,x[1]["product"].price is None,x[1]["product"].price or 0))
    counts={k:0 for k in order}
    for i,(m,row) in enumerate(ranked,1):
        p=row["product"]; counts[m.classification]+=1
        price=p.price_text or "price unavailable"
        print(f"{i:02}. {m.classification:<8} {m.score:>3}% | {price} | bundle={row['bundle']} | price_field={row['price_source']}")
        print("   ",p.title)
        print("    reasons:",", ".join(m.reasons))
        print("    id:",row["object_id"])
        print("   ",p.url)
    print("-"*110)
    print(" | ".join(f"{k.lower()}={counts[k]}" for k in ("EXACT","SIMILAR","POSSIBLE","REJECT")))
    print("IMPORTANT: verify the tracked standalone awning reports the storefront's current $849 advertised price before freezing pricing.")
if __name__=="__main__":main()
