from ...adapters.bunnings import _embedded_json_products, _link_products, _merge_products
from ...core.retailer_product import RetailerProduct

def run():
    passed=0

    embedded="<script type='application/json'>{\"props\":{\"products\":[{\"productName\":\"Makita 18V 330mm Lawn Mower Kit DLM330SM\",\"productUrl\":\"/makita-18v-330mm-lawn-mower-kit-dlm330sm_p0343916\",\"currentPrice\":{\"value\":357}}]}}</script>"
    a=_embedded_json_products(embedded)
    assert len(a)==1; passed+=1
    assert a[0].price==357; passed+=1
    assert a[0].price_text=="$357.00"; passed+=1

    card="<article class='product-card'><a href='/ryobi-mower_p1234567'>Ryobi 18V Lawn Mower</a><span class='price'>$399</span></article>"
    b=_link_products(card)
    assert len(b)==1 and b[0].price==399; passed+=1

    # Critical D4.1 regression: neighbour price must never leak into this card.
    neighbours="<article class='product-card'><span>$117</span><a href='/other_p1111111'>Other product</a></article>" + \
               "<article class='product-card'><a href='/makita-534mm_p0286804'>Makita 534mm 21 inch 18V x 2 Brushless Lawn Mower Kit</a><span>$1,176.02</span></article>"
    c=_link_products(neighbours)
    makita=[x for x in c if "p0286804" in x.url][0]
    assert makita.price==1176.02; passed+=1
    assert makita.price!=117; passed+=1

    # No price in this product card: nearby price from next card must not be borrowed.
    missing="<article class='product-card'><a href='/no-price_p2222222'>No Price Mower</a></article>" + \
            "<article class='product-card'><a href='/next_p3333333'>Next Mower</a><span>$599</span></article>"
    d=_link_products(missing)
    first=[x for x in d if "p2222222" in x.url][0]
    assert first.price is None; passed+=1

    # Multiple dollar values in an unstructured card are ambiguous: fail closed.
    ambiguous="<article class='product-card'><a href='/ambiguous_p4444444'>Ambiguous Mower</a><span>$499</span><span>$399</span></article>"
    e=_link_products(ambiguous)
    assert e[0].price is None; passed+=1

    merged=_merge_products([RetailerProduct("Bunnings","Ryobi 18V Lawn Mower",b[0].url,None,None),b[0]])
    assert len(merged)==1 and merged[0].price==399; passed+=1


    # D4.3: uncommaed four-digit prices must not truncate to three digits.
    four_digit="<article class='product-card'><a href='/makita-534mm_p0286804'>Makita 534mm 21 inch 18V x 2 Brushless Lawn Mower Kit</a><span>$1176.02</span></article>"
    f=_link_products(four_digit)
    assert f[0].price==1176.02; passed+=1

    # Comma-formatted four-digit price must parse identically.
    comma_four="<article class='product-card'><a href='/makita-534mm2_p0286805'>Makita Test Mower</a><span>$1,176.02</span></article>"
    g=_link_products(comma_four)
    assert g[0].price==1176.02; passed+=1

    normal="<article class='product-card'><a href='/normal_p5555555'>Normal Product</a><span>$117.00</span></article>"
    h=_link_products(normal)
    assert h[0].price==117.00; passed+=1

    normal2="<article class='product-card'><a href='/normal2_p6666666'>Normal Product 2</a><span>$429.00</span></article>"
    i=_link_products(normal2)
    assert i[0].price==429.00; passed+=1

    print(f"BUNNINGS PRICE SAFETY: {passed}/{passed} passed")

if __name__=="__main__": run()
