import argparse
from ...adapters.kickass import search_kickass, KickAssUnavailable, KickAssNoResults
def main():
    ap=argparse.ArgumentParser();ap.add_argument("query",nargs="?",default="pocket blower");ap.add_argument("--limit",type=int,default=20);a=ap.parse_args()
    print("H1.2 KICKASS STANDALONE ADAPTER");print("QUERY:",a.query)
    try:rows=search_kickass(a.query,a.limit)
    except KickAssNoResults as e:print("NO RESULTS:",e);return
    except KickAssUnavailable as e:print("UNAVAILABLE:",e);return
    for i,x in enumerate(rows,1):
        p="PRICE UNAVAILABLE" if x["price"] is None else f'${x["price"]:.2f}'
        print(f'{i:02}. {p:>18} | bundle={x["bundle"]} | price_field={x["price_source"]}')
        print("   ",x["title"]);print("   ",x["url"])
    print(f'HEALTH: returned={len(rows)} | priced={sum(x["price"] is not None for x in rows)} | bundles={sum(x["bundle"] for x in rows)}')
if __name__=="__main__":main()
