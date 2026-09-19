from ...adapters.supacentre import _normalise_hit
def check(cond,msg):
    if not cond: raise AssertionError(msg)
cases=0
hit={"name":"Kings Plus 270° Tourer XL Freestanding Awning MKII","url":"https://www.4wdsupacentre.com.au/a.html","objectID":"ABC","final_price":849}
r=_normalise_hit(hit); cases+=1; check(r["product"].price==849,"final price")
cases+=1; check(r["price_source"]=="final_price","price source")
cases+=1; check(not r["bundle"],"standalone")
b=_normalise_hit({"name":"Kings Awning + Bracket","url":"https://www.4wdsupacentre.com.au/b.html","price":539.95})
cases+=1; check(b["bundle"],"plus bundle")
d=_normalise_hit({"name":"Kings Awning","url":"https://www.4wdsupacentre.com.au/c.html","price":699,"deal_type":"Individual Product"})
cases+=1; check(not d["bundle"],"structured individual")
e=_normalise_hit({"name":"Kings Awning Package","url":"https://www.4wdsupacentre.com.au/d.html","price":700,"deal_type":"Bundle Deal"})
cases+=1; check(e["bundle"],"structured bundle")
print(f"4WD SUPACENTRE ADAPTER SAFETY: {cases}/{cases} passed")
