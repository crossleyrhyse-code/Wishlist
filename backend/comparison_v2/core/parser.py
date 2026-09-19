import re
from .models import ProductProfile

BRANDS=("makita","kings","ryobi","dewalt","milwaukee","ozito","san hima","dune","wanderer","coleman","bosch","aeg","ring","arlo","uniden","swann")
TYPE_ALIASES={
    "chainsaw":("chainsaw","chain saw"),
    "awning":("awning",),
    "chair":("chair","camp chair","camping chair"),
    "mower":("mower","lawn mower"),
    "blower":("blower","leaf blower"),
    "drill":("drill","driver drill"),
    "diagnostic_scanner":("diagnostic scanner","auto diagnostic scanner","automotive diagnostic scanner","diagnostic scan tool","scan tool","code reader","obd scanner","obd2 scanner","obdii scanner","obd2 code reader","obdii code reader"),
    "video_doorbell":("video doorbell","video door bell","doorbell","door bell"),
}
ACCESSORY_WORDS=("bracket","mount","mounting","cover","bag","holder","replacement","spare","adapter","adaptor","case","stand","strap")
MAJOR_BUNDLE_TYPES=("rooftop tent","roof top tent","roof rack","fridge","freezer","generator","compressor","table")

def _normalise(title):
    return re.sub(r"\s+"," ",str(title or "").lower()).strip()

def _find_type(text):
    for kind,aliases in TYPE_ALIASES.items():
        if any(re.search(rf"\b{re.escape(alias)}s?\b",text) for alias in aliases): return kind
    return None

def _find_brand(text):
    return next((b.title() for b in BRANDS if re.search(rf"\b{re.escape(b)}\b",text)),None)

def _find_model(title):
    # Model code must contain letters and at least 3 digits; ignore ordinary mm specs.
    for token in re.findall(r"\b[A-Za-z]{2,}[A-Za-z0-9-]*\d{3,}[A-Za-z0-9-]*\b",title):
        if not token.lower().endswith("mm"): return token.upper()
    return None

def parse_product(title):
    text=_normalise(title)
    v_right=re.search(r"\b(\d{1,3})\s*v\s*x\s*(\d+)\b",text)
    v_left=re.search(r"\b(\d+)\s*x\s*(\d{1,3})\s*v\b",text)
    if v_right:
        voltage=int(v_right.group(1)); voltage_multiplier=int(v_right.group(2))
    elif v_left:
        voltage=int(v_left.group(2)); voltage_multiplier=int(v_left.group(1))
    else:
        vm=re.search(r"\b(\d{1,3})\s*v(?=\b|x)",text)
        voltage=int(vm.group(1)) if vm else None; voltage_multiplier=None
    sm=re.search(r"\b(\d{2,4})\s*mm\b",text)
    scm=re.search(r"\b(\d+(?:\.\d+)?)\s*cm\b",text)
    size_mm=int(sm.group(1)) if sm else (int(round(float(scm.group(1))*10)) if scm else None)
    cm=re.search(r"\b(180|270|360)\s*(?:°|deg(?:ree)?s?)?\b",text)
    package="skin" if re.search(r"\bskin(?: only)?\b|\btool only\b|\bbare tool\b",text) else ("kit" if re.search(r"\bkit\b|\bcombo\b",text) else None)
    wm=re.search(r"\b(\d{2,5})\s*w(?:att)?s?\b",text)
    ahm=re.search(r"\b(\d+(?:\.\d+)?)\s*ah\b",text)
    bcm=re.search(r"\b(\d+)\s*x\s*\d+(?:\.\d+)?\s*ah\b",text)
    inchm=re.search(r'\b(\d+(?:\.\d+)?)\s*(?:"|inch(?:es)?\b)',text)
    accessory=any(re.search(rf"\b{re.escape(w)}\b",text) for w in ACCESSORY_WORDS)
    # A complete chair can legitimately include an integrated cup/wine/drink holder.
    # Do not classify the whole chair as an accessory merely because "holder" appears.
    if _find_type(text)=="chair" and re.search(r"\b(?:cup|wine|drink|bottle)\s+holder\b",text):
        accessory=any(
            re.search(rf"\b{re.escape(w)}\b",text)
            for w in ACCESSORY_WORDS if w != "holder"
        )
    # Awning add-ons are related products, but they are not alternative awnings.
    # Keep them out of comparison results for now. A future post-release
    # "suggested add-ons" feature can surface these separately.
    awning_addon_patterns = (
        r"\bawning\s+(?:mesh\s+)?wall(?:\s+set|\s+kit)?\b",
        r"\bawning\s+side\s+wall\b",
        r"\bawning\s+extension\b",
        r"\bawning\s+extender\b",
        r"\bawning\s+wall\s+kit\b",
        r"\b(?:awning\s+tent|tent\s+for\s+[^|]*awning)\b",
        r"\bside\s+wall(?:\s+\d+\s*pack)?\b",
        r"\b(?:vertical\s+)?pole\s+for\s+[^|]*awning\b",
        r"\bawning\s+(?:led\s+)?light\s+kit\b",
    )
    if _find_type(text)=="awning" and any(re.search(p,text) for p in awning_addon_patterns):
        accessory=True
    # Product-specific chainsaw parts: don't globally classify the ordinary word "chain" as an accessory.
    if _find_type(text)=="chainsaw" and re.search(r"\b(chainsaw chain|chainsaw bar|guide bar|saw chain|chain sharpener|chain file|file kit)\b",text):
        accessory=True

    # Non-product merchandise can contain a real product keyword in a franchise/title
    # (for example "Chainsaw Man") without actually being that physical product.
    # Treat strong merchandise/collectible evidence as non-comparable.
    merchandise_patterns = (
        r"\bpop!?\s+vinyl\b",
        r"\bnendoroid\b",
        r"\b(?:perching|noodle\s+stopper)\s+figure\b",
        r"\bfigurine\b",
        r"\bcollectible\s+(?:figure|statue)\b",
        r"\b(?:action\s+)?figure\b",
        # "Lookup" is also used as a collectible figure/product-line label.
        r"\blookup\b",
        # Strong entertainment/media evidence. These phrases can contain a
        # physical-product keyword as part of a franchise/title without being
        # that product (e.g. "Chainsaw Man" posters or a movie score).
        r"\bposter\b",
        r"\b(?:original\s+)?motion\s+picture\s+(?:score|soundtrack)\b",
        r"\bsoundtrack\b",
    )
    if product_type := _find_type(text):
        if any(re.search(p,text) for p in merchandise_patterns):
            accessory=True

    # Chair add-ons can contain the word "chair" but are not complete chairs.
    # Keep complete chairs with integrated features (e.g. "chair with side table")
    # while rejecting titles whose product is the pad/cushion/table itself.
    if _find_type(text)=="chair" and re.search(
        r"\b(?:chair\s+(?:seat\s+)?pad|chair\s+cushion|chair\s+side\s+table)\b", text
    ):
        accessory=True
    if re.search(r"\b(obd|obd2|obdii)\b",text) and re.search(
        r"\b(port lock|hard ?wire(?: kit)?|hardwire(?: kit)?|connector|adapter|adaptor|harness|breakout box)\b",text):
        accessory=True
    # Doorbell add-ons can contain the full product phrase but are not complete doorbells.
    if _find_type(text)=="video_doorbell" and re.search(
        r"\b(add[ -]?on|replacement battery|battery pack|mount|mounting bracket|wedge|chime only)\b", text):
        accessory=True
    extra=any(w in text for w in MAJOR_BUNDLE_TYPES)
    bundle=("+" in title or " bundle " in f" {text} ") and extra
    # Explicit bulk/multi-item furniture listings are not a single comparable product.
    # Examples: "4PK 8FT Tables & 32 Chairs", "Table & 6 Chairs".
    bulk_furniture=bool(
        re.search(r"\b\d+\s*(?:pk|pack)\b",text)
        and re.search(r"\btable(?:s)?\b",text)
        and re.search(r"\bchair(?:s)?\b",text)
    ) or bool(
        re.search(r"\btable(?:s)?\s*(?:&|and|\+)\s*\d+\s*chair(?:s)?\b",text)
    )
    if bulk_furniture:
        bundle=True
    product_type=_find_type(text)
    product_subtype=None
    if product_type=="awning":
        if re.search(r"\bshower\b",text):
            product_subtype="shower"
        elif re.search(r"\b(window|door)\s+awning\b",text):
            product_subtype="window_door"
        elif re.search(r"\b(folding arm|retractable folding arm)\b",text):
            product_subtype="folding_arm"
        elif re.search(r"\b(partition screen|partition blinds)\b",text):
            product_subtype="side_screen"
        elif re.search(r"\bside awning\b",text) and re.search(r"\b(car|suv|truck|4wd|vehicle|vehicles|tourer|driver side|passenger side)\b",text):
            product_subtype="vehicle"
        elif re.search(r"\bside awning\b",text):
            # A straight/side camping awning is still a vehicle awning unless
            # the title explicitly identifies a household/window context.
            product_subtype="vehicle"
        elif re.search(r"\b(car|suv|truck|4wd|vehicle|vehicles|tourer|driver side|passenger side)\b",text):
            product_subtype="vehicle_270" if re.search(r"\b270\s*(?:°|deg(?:ree)?s?)?\b",text) else "vehicle"
        elif re.search(r"\b270\s*(?:°|deg(?:ree)?s?)?\b",text) and re.search(r"\b(freestanding|tourer)\b",text):
            product_subtype="vehicle_270"
    return ProductProfile(
        raw_title=title, product_type=product_type, product_subtype=product_subtype, brand=_find_brand(text),
        model=_find_model(title), voltage=voltage,
        voltage_multiplier=voltage_multiplier,
        size_mm=size_mm,
        coverage_degrees=int(cm.group(1)) if cm else None,
        package=package,
        watts=int(wm.group(1)) if wm else None,
        amp_hours=float(ahm.group(1)) if ahm else None,
        battery_count=int(bcm.group(1)) if bcm else None,
        size_inches=float(inchm.group(1)) if inchm else None,
        is_accessory=accessory, is_bundle=bundle, attributes={}
    )
