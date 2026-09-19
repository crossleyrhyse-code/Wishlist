from __future__ import annotations
import json
from urllib.parse import quote
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from ..core.retailer_product import RetailerProduct

SEARCH_PAGE="https://www.4wdsupacentre.com.au/search.html?query={query}"
UA="Mozilla/5.0 (compatible; WishlistPriceComparison/0.1; local-development)"

class SupacentreUnavailable(RuntimeError): pass

class SupacentreNoResults(RuntimeError):
    """Retailer reachable, but discovery returned no usable catalogue products."""
    pass

def _money(v):
    try:
        if isinstance(v,dict):
            for k in ("value","amount","price","default","AUD"):
                if k in v:
                    x=_money(v[k])
                    if x is not None:return x
            return None
        if isinstance(v,(int,float)): return float(v)
        s=str(v).replace("$","").replace(",","").strip()
        import re
        m=re.search(r"\d+(?:\.\d{1,2})?",s)
        return float(m.group(0)) if m else None
    except (TypeError,ValueError):
        return None

def _price_from_hit(hit):
    # Algolia records can vary by deployment/store view. Prefer explicit
    # current/final/special price fields; do not use old/was/MSRP fields.
    direct=("final_price","finalPrice","special_price","specialPrice","sale_price","salePrice","price")
    for key in direct:
        if key in hit:
            p=_money(hit.get(key))
            if p is not None:return p,key
    # Common Magento/Algolia nested price containers.
    for container in ("price","prices","price_range","priceRange"):
        v=hit.get(container)
        if not isinstance(v,dict):continue
        for key in ("final_price","finalPrice","special_price","specialPrice","default","value","amount"):
            if key in v:
                p=_money(v.get(key))
                if p is not None:return p,f"{container}.{key}"
        # Store/currency nesting, e.g. price.AUD.default
        for subkey,sub in v.items():
            if isinstance(sub,dict):
                for key in ("final_price","finalPrice","special_price","specialPrice","default","value","amount"):
                    if key in sub:
                        p=_money(sub.get(key))
                        if p is not None:return p,f"{container}.{subkey}.{key}"
    return None,None

def _bundle_from_hit(hit):
    # Prefer structured deal/product metadata when present.
    for key in ("deal_type","dealType","product_deal_type","productDealType","type_label","typeLabel"):
        val=str(hit.get(key) or "").lower()
        if "bundle" in val:return True
        if "individual" in val:return False
    tags=" ".join(str(x) for x in (hit.get("_tags") or [])) if isinstance(hit.get("_tags"),list) else str(hit.get("_tags") or "")
    text=(str(hit.get("name") or "")+" "+tags).lower()
    # Conservative fallback requested for beta: obvious bundles are not comparison alternatives.
    return ("bundle n save" in text or "bundle deal" in text or " bundle " in f" {text} " or "+" in str(hit.get("name") or ""))

def _is_category_hit(hit):
    tags=hit.get("_tags") or []
    if isinstance(tags,str): tags=[tags]
    if any(str(t).lower()=="category" for t in tags): return True
    kind=str(hit.get("type") or hit.get("record_type") or hit.get("recordType") or "").lower()
    if kind in ("category","categories","navigation"): return True
    url=str(hit.get("url") or "").lower()
    # The catalogue category records observed live use sc-prod category paths,
    # not normal www product URLs.
    if "sc-prod.4wdsc.com/" in url and "/camping/" in url and url.endswith(".html"):
        return True
    return False

def _normalise_hit(hit):
    if _is_category_hit(hit): return None
    title=str(hit.get("name") or "").strip()
    url=str(hit.get("url") or "").strip()
    if not title or not url:return None
    price,price_source=_price_from_hit(hit)
    return {
        "product":RetailerProduct("4WD Supacentre",title,url,price,f"${price:.2f}" if price is not None else None),
        "object_id":str(hit.get("objectID") or hit.get("sku") or ""),
        "bundle":_bundle_from_hit(hit),
        "price_source":price_source,
        "raw":hit,
    }

def _search_4wd_supacentre_single(query,limit=30,timeout=30):
    """Use the retailer's normal public storefront in ordinary Chromium.

    The public search page loads product results from Algolia. We deliberately
    capture the same public JSON response the page uses instead of guessing a
    private endpoint or copying a transient search credential into source code.
    """
    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise SupacentreUnavailable("Playwright/Chromium is required for 4WD Supacentre search.") from exc

    page_url=SEARCH_PAGE.format(query=quote(query))
    records=[]
    try:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1365,"height":900})
            def response(resp):
                if "algolia.net/1/indexes/*/queries" not in resp.url.lower() or resp.status!=200:return
                try:
                    data=resp.json()
                    for result in data.get("results",[]):
                        for hit in result.get("hits",[]):
                            if isinstance(hit,dict) and hit.get("name") and hit.get("url"):
                                records.append(hit)
                except Exception:
                    pass
            page.on("response",response)
            page.goto(page_url,wait_until="domcontentloaded",timeout=timeout*1000)
            page.wait_for_timeout(5000)

            # The 4WD storefront can lazy-load/paginate its Algolia results.
            # Trigger ordinary browser scrolling rather than inventing or
            # replaying a private API request.
            for _ in range(5):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1200)
            page.wait_for_timeout(1500)
            browser.close()
    except Exception as exc:
        raise SupacentreUnavailable(f"4WD Supacentre browser search failed: {exc}") from exc

    unique=[]; seen=set()
    for hit in records:
        row=_normalise_hit(hit)
        if not row:continue
        product=row["product"]
        key=product.url.split("?",1)[0].rstrip("/").lower()
        if key in seen:continue
        seen.add(key); unique.append(row)

    # 4WD Supacentre searches can be dominated by Bundle N Save records.
    # Preserve bundles for diagnostics, but do not let them consume the useful
    # standalone-result allowance. Return standalone products first, followed
    # by bundles so the test can still verify bundle rejection.
    standalone=[r for r in unique if not r["bundle"]]
    bundles=[r for r in unique if r["bundle"]]
    out=standalone[:limit]
    diagnostic_bundle_slots=min(5,max(0,limit-len(out)))
    if diagnostic_bundle_slots:
        out.extend(bundles[:diagnostic_bundle_slots])
    elif bundles and limit>=5:
        # Keep a small bundle sample while prioritising useful standalone hits.
        keep=min(5,len(bundles))
        out=standalone[:max(0,limit-keep)]+bundles[:keep]

    if not out:
        raise SupacentreUnavailable("4WD Supacentre loaded, but no public Algolia product records were captured.")
    return out


def _default_query_variants(query):
    """Conservative public-search broadening; matcher still decides relevance."""
    q=" ".join(str(query or "").split()).strip()
    low=q.lower()
    variants=[q]
    if "awning" in low:
        variants.extend(["awning","vehicle awning","side awning"])
        if "270" in low: variants.append("270 awning")
    elif "camp light" in low or "camp lighting" in low:
        variants.extend(["LED camp light","camp lighting","LED light"])
    elif "fridge" in low:
        variants.extend(["fridge freezer","portable fridge"])
    elif "battery box" in low:
        variants.append("12V battery box")
    out=[]; seen=set()
    for x in variants:
        k=x.lower()
        if x and k not in seen: seen.add(k); out.append(x)
    return out

def search_4wd_supacentre_multi(query,limit=30,timeout=30,queries=None):
    variants=queries or _default_query_variants(query)
    merged=[]; seen=set(); diagnostics=[]
    for q in variants:
        try:
            rows=_search_4wd_supacentre_single(q,limit=max(limit,20),timeout=timeout)
            diagnostics.append((q,"ok",len(rows)))
        except SupacentreUnavailable as exc:
            diagnostics.append((q,"unavailable",str(exc)))
            continue
        for row in rows:
            p=row["product"]
            key=p.url.split("?",1)[0].rstrip("/").lower()
            if key in seen: continue
            seen.add(key); merged.append(row)

    if not merged:
        raise SupacentreNoResults("4WD Supacentre search completed but returned no usable product records across broadened searches.")

    standalone=[r for r in merged if not r["bundle"]]
    bundles=[r for r in merged if r["bundle"]]
    # Prioritise useful standalone candidates but retain a small bundle sample
    # for live verification that rejection remains intact.
    keep_bundles=min(5,len(bundles),max(0,limit//4))
    useful=standalone[:max(0,limit-keep_bundles)]
    useful.extend(bundles[:max(0,limit-len(useful))])
    return useful,diagnostics

# Public adapter entry point now uses broadened discovery.
def search_4wd_supacentre(query,limit=30,timeout=30):
    rows,_=search_4wd_supacentre_multi(query,limit=limit,timeout=timeout)
    return rows
