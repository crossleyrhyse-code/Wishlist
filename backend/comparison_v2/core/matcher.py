import re
from .models import MatchResult

def _normalised_identity(title):
    text=str(title or "").lower().replace("°"," degree ")
    text=re.sub(r"\bdegrees\b","degree",text)
    return re.sub(r"[^a-z0-9]+"," ",text).strip()

def compare_products(tracked,candidate):
    reasons=[]
    if candidate.is_accessory: return MatchResult("REJECT",0,["Candidate is an accessory."])
    if candidate.is_bundle: return MatchResult("REJECT",0,["Candidate is a multi-product bundle."])
    if tracked.product_type and candidate.product_type and tracked.product_type != candidate.product_type:
        return MatchResult("REJECT",0,["Product types differ."])
    if tracked.product_type and not candidate.product_type:
        return MatchResult("REJECT",10,["Candidate product type is unknown."])

    # Exact title identity is a strong fallback when model numbers do not exist.
    # Accessory/bundle/type rejection above still takes precedence.
    if (tracked.product_type and tracked.product_type==candidate.product_type
        and _normalised_identity(tracked.raw_title)==_normalised_identity(candidate.raw_title)):
        if not (tracked.brand and candidate.brand and tracked.brand!=candidate.brand):
            return MatchResult("EXACT",100,["Same normalized product title."])

    # Retailers commonly append descriptive marketing copy after the actual
    # product name (often after "|"). If the tracked title exactly matches the
    # candidate's leading product-name segment, keep it EXACT.
    if tracked.product_type and tracked.product_type==candidate.product_type:
        t=_normalised_identity(tracked.raw_title)
        c_lead=_normalised_identity(str(candidate.raw_title or "").split("|",1)[0])
        if t and len(t)>=18 and t==c_lead:
            if not (tracked.brand and candidate.brand and tracked.brand!=candidate.brand):
                return MatchResult("EXACT",100,["Same core product title; retailer description appended."])

    if tracked.product_type=="awning" and candidate.product_type=="awning":
        ts=tracked.product_subtype
        cs=candidate.product_subtype
        household={"folding_arm","window_door","side_screen"}
        vehicle={"vehicle","vehicle_270"}
        if (ts in vehicle and cs=="shower") or (ts=="shower" and cs in vehicle):
            return MatchResult("REJECT",0,["Awning contexts are incompatible."])
        if ts in vehicle and cs in household:
            return MatchResult("REJECT",0,["Awning contexts are incompatible."])
        if ts in household and cs in vehicle:
            return MatchResult("REJECT",0,["Awning contexts are incompatible."])

    score=40 if tracked.product_type and tracked.product_type==candidate.product_type else 20
    same_brand=bool(tracked.brand and candidate.brand and tracked.brand==candidate.brand)
    different_brand=bool(tracked.brand and candidate.brand and tracked.brand!=candidate.brand)
    material_conflict=False

    if tracked.brand and candidate.brand:
        if tracked.brand==candidate.brand: score+=15; reasons.append("Same brand.")
        else: reasons.append("Different brand.")

    if tracked.voltage and candidate.voltage:
        if tracked.voltage==candidate.voltage:
            score+=15; reasons.append("Same voltage.")
            tm=tracked.voltage_multiplier or 1
            cm=candidate.voltage_multiplier or 1
            if tm==cm:
                if tm>1: score+=5; reasons.append("Same battery voltage multiplier.")
            else:
                score-=20; material_conflict=True; reasons.append("Different battery voltage configuration.")
        else: score-=20; material_conflict=True; reasons.append("Different voltage.")

    if tracked.size_mm and candidate.size_mm:
        diff=abs(tracked.size_mm-candidate.size_mm)
        if diff<=25: score+=10; reasons.append("Similar physical size.")
        elif diff>=100: score-=15; material_conflict=True; reasons.append("Substantially different physical size.")

    if tracked.coverage_degrees and candidate.coverage_degrees:
        if tracked.coverage_degrees==candidate.coverage_degrees: score+=20; reasons.append("Same coverage angle.")
        else: score-=20; reasons.append("Different coverage angle.")

    if tracked.model and candidate.model:
        if tracked.model==candidate.model:
            score+=30; reasons.append("Same model.")
        else:
            reasons.append("Different model.")
            if same_brand and not material_conflict:
                score=max(score,60)
            else:
                score-=5
                if tracked.brand and not candidate.brand:
                    score=min(score,59); reasons.append("Candidate brand is unknown.")

    if tracked.package and candidate.package and tracked.package!=candidate.package:
        score-=5; reasons.append("Different package type.")

    score=max(0,min(score,100))

    if tracked.model and candidate.model and tracked.model==candidate.model:
        return MatchResult("EXACT",max(90,score),reasons)

    if tracked.product_type=="chair" and candidate.product_type=="chair":
        if not tracked.brand:
            return MatchResult("SIMILAR",max(60,score),reasons+["Same generic product category."])
        if tracked.brand and candidate.brand and tracked.brand==candidate.brand:
            return MatchResult("SIMILAR",max(60,score),reasons+["Same chair brand and category."])

    if tracked.product_type=="video_doorbell" and candidate.product_type=="video_doorbell":
        if tracked.brand and candidate.brand and tracked.brand==candidate.brand:
            return MatchResult("SIMILAR",max(60,score),reasons+["Same video doorbell brand and category."])

    if (tracked.product_type==candidate.product_type and tracked.voltage and candidate.voltage
        and tracked.voltage==candidate.voltage and (not tracked.brand or not candidate.brand)):
        if tracked.brand and not candidate.brand and tracked.model and candidate.model and tracked.model!=candidate.model:
            return MatchResult("POSSIBLE",min(score,59),reasons+["Unknown candidate brand and different model limit confidence."])
        return MatchResult("SIMILAR",max(60,score),reasons+["Core specification matches despite missing brand."])

    if different_brand and score>=35:
        if (tracked.product_type=="awning" and candidate.product_type=="awning"
            and tracked.coverage_degrees and candidate.coverage_degrees
            and tracked.coverage_degrees==candidate.coverage_degrees):
            return MatchResult("SIMILAR",max(60,score),reasons+["Matching awning coverage supports similarity across brands."])
        return MatchResult("POSSIBLE",min(score,59),reasons+["Different brand caps confidence at possible."])
    if tracked.brand and not candidate.brand and tracked.model and candidate.model and tracked.model!=candidate.model and score>=35:
        return MatchResult("POSSIBLE",min(score,59),reasons+["Unknown candidate brand prevents strong model-alternative confidence."])
    if score>=60: return MatchResult("SIMILAR",score,reasons)
    if score>=35: return MatchResult("POSSIBLE",score,reasons)
    return MatchResult("REJECT",score,reasons)
