from ...adapters.supacentre import _default_query_variants
from ...core.parser import parse_product
from ...core.matcher import compare_products
def ck(x,m):
    if not x: raise AssertionError(m)
n=0
v=_default_query_variants("270 awning")
n+=1; ck(v[0]=="270 awning","seed first")
n+=1; ck("awning" in v,"broad awning")
n+=1; ck("vehicle awning" in v,"vehicle variant")
n+=1; ck("side awning" in v,"side variant")
n+=1; ck(len(v)==len(set(x.lower() for x in v)),"deduped")
tracked=parse_product("Kings Plus 270° Tourer XL Freestanding Awning MKII")
side=parse_product("Kings 2x3m Side Awning | UPF50+ | Suits All Vehicles")
m=compare_products(tracked,side)
n+=1; ck(m.classification in ("SIMILAR","POSSIBLE"),"side awning survives broad discovery")
tent=parse_product("Kings Awning Tent (suits 2m x 2.5m Awning)")
n+=1; ck(compare_products(tracked,tent).classification=="REJECT","awning tent rejected")
print(f"4WD G1.5.3 MULTI-QUERY SAFETY: {n}/{n} passed")
