from ...adapters.supacentre import _normalise_hit,_is_category_hit
def ck(x,msg):
    if not x: raise AssertionError(msg)
n=0
cat={"name":"270 Tourer Free Standing Awnings","url":"https://sc-prod.4wdsc.com/camping/awnings/270-free-standing-awning.html","_tags":["category"]}
n+=1; ck(_is_category_hit(cat),"category tag")
n+=1; ck(_normalise_hit(cat) is None,"category excluded")
nav={"name":"Awnings","url":"https://example.test/awnings","type":"category"}
n+=1; ck(_normalise_hit(nav) is None,"typed category excluded")
prod={"name":"Kings Plus 270° Tourer XL Freestanding Awning MKII","url":"https://www.4wdsupacentre.com.au/kings-plus-tourer-270-xl-freestanding-awning-mkii.html","price":849,"_tags":["product"]}
r=_normalise_hit(prod)
n+=1; ck(r is not None,"product retained")
n+=1; ck(r["product"].price==849,"product price retained")
print(f"4WD G1.5.2 CATEGORY/EXPANSION SAFETY: {n}/{n} passed")
