import argparse
from ...core.parser import parse_product
from ...core.matcher import compare_products
from ...adapters.bunnings import search_bunnings,BunningsUnavailable
def main():
    ap=argparse.ArgumentParser();ap.add_argument("tracked");ap.add_argument("--query");ap.add_argument("--limit",type=int,default=20);a=ap.parse_args()
    q=a.query or a.tracked;t=parse_product(a.tracked)
    print(f"TRACKED : {a.tracked}\nSEARCH  : {q}\n"+"-"*90)
    try:ps=search_bunnings(q,a.limit)
    except BunningsUnavailable as e:print(f"BUNNINGS UNAVAILABLE: {e}");raise SystemExit(2)
    rows=[]
    for p in ps:
        pr=parse_product(p.title);m=compare_products(t,pr);rows.append((m,p,pr))
    order={"EXACT":0,"SIMILAR":1,"POSSIBLE":2,"REJECT":3};rows.sort(key=lambda x:(order.get(x[0].classification,9),-x[0].score))
    for i,(m,p,pr) in enumerate(rows,1):
        print(f"{i:02d}. {m.classification:<8} {m.score:>3}% | {p.price_text or 'price unavailable'}")
        print(f"    {p.title}\n    parsed: type={pr.product_type} brand={pr.brand} model={pr.model} voltage={pr.voltage}")
        print(f"    reasons: {', '.join(m.reasons) or 'none'}\n    {p.url}")
    print("-"*90)
    print(f"RESULTS: {len(rows)} | exact={sum(m.classification=='EXACT' for m,_,_ in rows)} | similar={sum(m.classification=='SIMILAR' for m,_,_ in rows)} | possible={sum(m.classification=='POSSIBLE' for m,_,_ in rows)} | rejected={sum(m.classification=='REJECT' for m,_,_ in rows)}")
if __name__=="__main__":main()
