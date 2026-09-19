from ...adapters.supacentre import _default_query_variants, SupacentreNoResults
def ck(x,m):
    if not x: raise AssertionError(m)
n=0
v=_default_query_variants("camp light")
n+=1; ck(v[0]=="camp light","seed")
n+=1; ck("LED camp light" in v,"led fallback")
n+=1; ck("camp lighting" in v,"lighting fallback")
n+=1; ck(len(v)==len(set(x.lower() for x in v)),"dedupe")
v=_default_query_variants("270 awning")
n+=1; ck(all(x in v for x in ("awning","vehicle awning","side awning")),"awning retained")
v=_default_query_variants("battery box")
n+=1; ck("12V battery box" in v,"battery fallback")
n+=1; ck(issubclass(SupacentreNoResults,RuntimeError),"no-results exception")
print(f"4WD G1.5.4 GENERIC FALLBACK SAFETY: {n}/{n} passed")
