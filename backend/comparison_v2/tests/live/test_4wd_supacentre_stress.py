import argparse
from ...adapters.supacentre import search_4wd_supacentre_multi, SupacentreUnavailable, SupacentreNoResults
from ...core.parser import parse_product
from ...core.matcher import compare_products

# Deliberately unrelated product families. These are discovery/price/bundle
# stress tests, not new matching rules.
SCENARIOS = [
    ("Kings Plus 270° Tourer XL Freestanding Awning MKII", "270 awning"),
    ("Kings 45L Stayzcool Fridge Freezer", "45L fridge"),
    ("Kings Battery Box", "battery box"),
    ("Kings LED Camp Light", "camp light"),
]

ORDER={"EXACT":0,"SIMILAR":1,"POSSIBLE":2,"REJECT":3}

def run(title, query, limit):
    print("="*118)
    print("TRACKED:", title)
    print("SEED QUERY:", query)
    tracked=parse_product(title)
    try:
        rows,diag=search_4wd_supacentre_multi(query,limit=limit)
    except SupacentreNoResults as exc:
        print("NO RESULTS:",exc)
        return
    except SupacentreUnavailable as exc:
        print("UNAVAILABLE:",exc)
        return
    print("DISCOVERY:", " | ".join(f"{q}={status}:{n}" for q,status,n in diag))
    ranked=[]
    for row in rows:
        p=row["product"]
        profile=parse_product(p.title)
        if row["bundle"]:
            profile.is_bundle=True
        ranked.append((compare_products(tracked,profile),row))
    ranked.sort(key=lambda x:(ORDER.get(x[0].classification,9),-x[0].score,
                              x[1]["product"].price is None,x[1]["product"].price or 0))
    counts={k:0 for k in ORDER}
    bundle_count=0
    priced_count=0
    for i,(m,row) in enumerate(ranked,1):
        p=row["product"]
        counts[m.classification]+=1
        bundle_count += int(bool(row["bundle"]))
        priced_count += int(p.price is not None)
        print(f"{i:02}. {m.classification:<8} {m.score:>3}% | "
              f"{p.price_text or 'price unavailable':>17} | bundle={row['bundle']} | "
              f"price_field={row.get('price_source')}")
        print("   ",p.title)
        print("   ",p.url)
    print("COUNTS:", " | ".join(f"{k.lower()}={counts[k]}" for k in ORDER))
    print(f"HEALTH: returned={len(rows)} | priced={priced_count} | bundles_sampled={bundle_count}")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--limit",type=int,default=20)
    args=ap.parse_args()
    print("G1.5.4 4WD SUPACENTRE GENERIC FALLBACK / CROSS-CATEGORY STRESS TEST")
    for title,q in SCENARIOS:
        run(title,q,args.limit)

if __name__=="__main__":
    main()
