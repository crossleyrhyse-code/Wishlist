from ...core.parser import parse_product
from ...core.matcher import compare_products
from ...adapters.supacentre import _normalise_hit

def ck(cond,msg):
    if not cond: raise AssertionError(msg)
n=0

tracked=parse_product("Kings Plus 270° Tourer XL Freestanding Awning MKII")
candidate=parse_product("Kings Plus 270° Tourer XL Freestanding Awning MKII | Gigantic 14.57sqm Coverage | Perfect For Large 4WDs & Camper Trailers | Powdercoated Aluminium Frame")
m=compare_products(tracked,candidate); n+=1; ck(m.classification=="EXACT" and m.score==100,"appended retailer copy exact")

side=parse_product("Kings 2x3m Waterproof Side Awning Suits All Vehicles Adventure Kings")
n+=1; ck(side.product_type=="awning","side awning type")
n+=1; ck(side.product_subtype=="vehicle","side awning vehicle subtype")
m2=compare_products(tracked,side); n+=1; ck(m2.classification in ("SIMILAR","POSSIBLE"),"vehicle side awning survives")

tent=parse_product("Kings Tent for 2x2.5m Awning")
n+=1; ck(tent.is_accessory or compare_products(tracked,tent).classification=="REJECT","awning tent must reject")

b=_normalise_hit({"name":"Kings Plus 270 Awning + Bracket","url":"https://www.4wdsupacentre.com.au/bundle.html","price":539.95})
n+=1; ck(b["bundle"],"bundle remains detected")
print(f"4WD G1.5.1 MATCH/RESULT SAFETY: {n}/{n} passed")
