from ...adapters.jbhifi import _normalise_hit
from ...core.parser import parse_product
from ...core.matcher import compare_products

def check(cond, msg):
    if not cond:
        raise AssertionError(msg)

n=0
row=_normalise_hit({"objectID":"897340","title":"Ring Battery Video Doorbell 2K (Speckled Grey)","sku":"897340","handle":"ring-battery-video-doorbell-2k-speckled-grey","price":149,"vendor":"RING","product_type":"Home Tech"})
n+=1; check(row["product"].price==149.0,"price")
n+=1; check(row["product"].url=="https://www.jbhifi.com.au/products/ring-battery-video-doorbell-2k-speckled-grey","url")
n+=1; check(row["sku"]=="897340","sku")

tracked=parse_product("Ring Battery Video Doorbell 2K (Speckled Grey)")
cases=[
("Ring Battery Video Doorbell 2K (Speckled Grey)","EXACT"),
("Ring Battery Video Doorbell 2K (Matte Mocha)","SIMILAR"),
("Ring Wired Video Doorbell 2K Plug-in (Speckled Grey)","SIMILAR"),
("Arlo Wired Video Doorbell","POSSIBLE"),
("Uniden SOLO X2K Door Bell Plus","POSSIBLE"),
("Swann MaxRanger4K Long-Range Wireless Video Doorbell (Add-On)","REJECT"),
("Ring Quick Release Ultra Battery Pack","REJECT"),
("Lord Of The Rings - Eye Of Sauron 2 Pen Set","REJECT"),
]
for title,want in cases:
    got=compare_products(tracked,parse_product(title)).classification
    n+=1; check(got==want,f"{title}: wanted {want}, got {got}")
print(f"JB HI-FI OFFLINE SAFETY: {n}/{n} passed")
