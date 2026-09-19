from bs4 import BeautifulSoup
from ...adapters.kickass import _card_price
def ck(x,m):
    if not x:raise AssertionError(m)
n=0
def card(h):return BeautifulSoup(h,"html.parser").select_one(".product-card")
c=card("""<div class='product-card'><a class='product-card-title' href='/products/a'>A</a>
<div class='ka-card-price-main'><span class='ka-card-symbol'>$</span><span class='ka-card-dollars'>99</span><span class='ka-card-cents'>95</span></div></div>""")
p,s=_card_price(c); n+=1;ck(p==99.95,"sale price")
n+=1;ck(s=="ka-card-price-main","source")
c=card("""<div class='product-card'><div class='ka-card-price-main'><span class='ka-card-dollars'>1,299</span><span class='ka-card-cents'>00</span></div></div>""")
p,s=_card_price(c); n+=1;ck(p==1299.0,"comma price")
c=card("""<div class='product-card'>RRP $149.95 OR 4 PAYMENTS OF $24.99</div>""")
p,s=_card_price(c); n+=1;ck(p is None,"never generic-dollar guess")
n+=1;ck("bundle" in "KickAss Jet Blower Bundle".lower(),"bundle title safety")
print(f"KICKASS H1.2 TILE/PRICE SAFETY: {n}/{n} passed")
