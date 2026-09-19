from ...core.parser import parse_product
from ...core.matcher import compare_products

def check(title, expected):
    tracked=parse_product("Kings Plus 270 Degree Tourer XL Freestanding Awning MKII")
    got=compare_products(tracked,parse_product(title))
    assert got.classification==expected,(title,got)
    print("PASS",expected,title)

def run():
    check("Kings Plus 270° Tourer XL Freestanding Awning MKII | Gigantic 14.57sqm Coverage | Perfect For Large 4WDs & Camper Trailers | Powdercoated Aluminium Frame","EXACT")
    check("XTM Vertical Pole for 270 Degree Awning","REJECT")
    check("KickAss Flexible Awning LED Light Kit","REJECT")
    check("KickAss Premium Shower Awning - Black & Blue","REJECT")
    check("KickAss Premium Shower Awning with Roof & LED Light Strip","REJECT")
    check("KickAss Premium LEFT Fold-Out Shower Tent Awning and Camping Change Room with LED lighting","REJECT")
    check("Ridge Ryder 270° Awning","SIMILAR")
    print("FIVE-RETAILER AWNING CLEANUP: 7/7 passed")
if __name__=="__main__":run()
