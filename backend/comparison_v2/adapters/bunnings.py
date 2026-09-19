from __future__ import annotations
import json,re
from html import unescape
from urllib.parse import quote,urljoin
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError
from ..core.retailer_product import RetailerProduct

BASE="https://www.bunnings.com.au"
SEARCH=BASE+"/search/products?q={query}"
UA="Mozilla/5.0 (compatible; WishlistPriceComparison/0.1; local-development)"
class BunningsUnavailable(RuntimeError): pass

def _money(v):
    try:
        if isinstance(v,dict):
            for key in ("value","amount","price","currentPrice","nowPrice"):
                if key in v:return _money(v[key])
            return None
        m=re.search(r"\d+(?:\.\d{1,2})?",str(v).replace("$","").replace(",","").strip())
        return float(m.group(0)) if m else None
    except (TypeError,ValueError):return None

def _walk(x):
    if isinstance(x,dict):
        yield x
        for v in x.values():yield from _walk(v)
    elif isinstance(x,list):
        for v in x:yield from _walk(v)

def _looks_product_url(url):
    u=str(url or "")
    return "/p/" in u or bool(re.search(r"_p\d+",u,re.I))

def _price_from_dict(d):
    for key in ("price","currentPrice","nowPrice","salePrice","displayPrice","standardPrice","lowPrice","highPrice","amount","value"):
        if key in d:
            v=_money(d.get(key))
            if v is not None:return v
    offers=d.get("offers")
    if isinstance(offers,dict):
        for key in ("price","lowPrice","highPrice"):
            v=_money(offers.get(key))
            if v is not None:return v
    return None

def _json_products(html):
    out=[]
    for raw in re.findall(r"<script[^>]*type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",html,re.I|re.S):
        try:data=json.loads(unescape(raw).strip())
        except Exception:continue
        for d in _walk(data):
            if not isinstance(d,dict) or not d.get("name") or not d.get("url"):continue
            url=str(d["url"])
            if not _looks_product_url(url):continue
            price=_price_from_dict(d)
            out.append(RetailerProduct("Bunnings",str(d["name"]).strip(),urljoin(BASE,url),price,f"${price:.2f}" if price is not None else None))
    return out

def _embedded_json_products(html):
    out=[]
    raws=re.findall(r"<script[^>]*type=[\"']application/json[\"'][^>]*>(.*?)</script>",html,re.I|re.S)
    m=re.search(r"<script[^>]+id=[\"']__NEXT_DATA__[\"'][^>]*>(.*?)</script>",html,re.I|re.S)
    if m:raws.append(m.group(1))
    for raw in raws:
        try:data=json.loads(unescape(raw).strip())
        except Exception:continue
        for d in _walk(data):
            if not isinstance(d,dict):continue
            name=d.get("name") or d.get("productName") or d.get("title")
            url=d.get("url") or d.get("productUrl") or d.get("productURL") or d.get("href")
            if not name or not url or not _looks_product_url(url):continue
            price=_price_from_dict(d)
            out.append(RetailerProduct("Bunnings",str(name).strip(),urljoin(BASE,str(url)),price,f"${price:.2f}" if price is not None else None))
    return out

def _card_price(html,start,end):
    """Return a price only when it is contained inside the same product-card element.

    We deliberately do NOT scan arbitrary characters before/after the link.
    If a safe card boundary cannot be identified, return None.
    """
    # Candidate enclosing containers used by product tiles/cards.
    containers = ("article", "li")
    for tag in containers:
        open_matches=list(re.finditer(rf"<{tag}\b[^>]*>",html[:start],re.I))
        if not open_matches:
            continue
        opening=open_matches[-1]
        close=re.search(rf"</{tag}\s*>",html[end:],re.I)
        if not close:
            continue
        card_end=end+close.end()
        # Reject implausibly large containers: likely a list/grid, not one product.
        if card_end-opening.start()>15000:
            continue
        card=unescape(html[opening.start():card_end])
        # Ensure the product link itself is actually in this container.
        if html[start:end] not in html[opening.start():card_end]:
            continue
        prices=[]
        for m in re.finditer(r"\$\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?)",card):
            try: prices.append(float(m.group(1).replace(",","")))
            except ValueError: pass
        # A single explicit dollar value inside one product card is safe.
        # Multiple values may be member/was/now pricing, so leave unavailable
        # unless structured JSON already supplied the price.
        if len(prices)==1:
            return prices[0]
        return None

    # Div fallback only when it looks explicitly like a product card/tile.
    before=html[:start]
    divs=list(re.finditer(r"<div\b[^>]*(?:product[^>]*(?:card|tile)|(?:card|tile)[^>]*product)[^>]*>",before,re.I))
    if divs:
        opening=divs[-1]
        close=re.search(r"</div\s*>",html[end:],re.I)
        if close:
            card_end=end+close.end()
            if card_end-opening.start()<=12000:
                card=unescape(html[opening.start():card_end])
                prices=[]
                for m in re.finditer(r"\$\s*((?:[0-9]{1,3}(?:,[0-9]{3})+|[0-9]+)(?:\.[0-9]{1,2})?)",card):
                    try: prices.append(float(m.group(1).replace(",","")))
                    except ValueError: pass
                if len(prices)==1:
                    return prices[0]
    return None

def _link_products(html):
    out=[]
    pat=re.compile(r"<a[^>]+href=[\"']([^\"']*(?:/p/|_p\d+)[^\"']*)[\"'][^>]*>(.*?)</a>",re.I|re.S)
    for match in pat.finditer(html):
        href,body=match.group(1),match.group(2)
        title=unescape(re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",body))).strip()
        if len(title)<4:continue
        price=_card_price(html,match.start(),match.end())
        out.append(RetailerProduct("Bunnings",title,urljoin(BASE,unescape(href)),price,f"${price:.2f}" if price is not None else None))
    return out

def _merge_products(products):
    merged={};order=[]
    for p in products:
        key=p.url.split("?")[0].lower()
        if key not in merged:
            merged[key]=p;order.append(key);continue
        current=merged[key]
        if current.price is None and p.price is not None:
            merged[key]=RetailerProduct("Bunnings",current.title if len(current.title)>=len(p.title) else p.title,current.url,p.price,p.price_text)
    return [merged[k] for k in order]

def search_bunnings(query,limit=30,timeout=15):
    req=Request(SEARCH.format(query=quote(query)),headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
    try:
        with urlopen(req,timeout=timeout) as r:status=getattr(r,"status",200);html=r.read().decode("utf-8","replace")
    except HTTPError as e:raise BunningsUnavailable(f"Bunnings returned HTTP {e.code}.") from e
    except URLError as e:raise BunningsUnavailable(f"Bunnings connection failed: {e.reason}.") from e
    if status!=200:raise BunningsUnavailable(f"Bunnings returned HTTP {status}.")
    if "request could not be satisfied" in html.lower() or "access denied" in html.lower():raise BunningsUnavailable("Bunnings declined the automated search request.")
    found=_merge_products(_json_products(html)+_embedded_json_products(html)+_link_products(html))
    clean=[];seen=set()
    for p in found:
        k=(p.url.split("?")[0].lower(),p.title.lower())
        if k in seen:continue
        low_title=p.title.lower()
        if "assembly service" in p.url.lower() or ("assemble your" in low_title and "shop now" in low_title):continue
        seen.add(k);clean.append(p)
        if len(clean)>=limit:break
    if not clean:raise BunningsUnavailable("Bunnings page loaded, but no supported product records were found.")
    return clean
