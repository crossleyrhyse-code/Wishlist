from __future__ import annotations
import re
from html import unescape
from urllib.parse import quote_plus, urljoin
import requests
from bs4 import BeautifulSoup

BASE="https://www.kickassproducts.com.au"
SEARCH=BASE+"/search?type=product&q={q}"

class KickAssUnavailable(RuntimeError): pass
class KickAssNoResults(RuntimeError): pass

def _money(dollars,cents):
    try:return float(f"{re.sub(r'[^0-9]','',dollars)}.{re.sub(r'[^0-9]','',cents or '00')[:2]:0<2}")
    except Exception:return None

def _card_price(card):
    main=card.select_one(".ka-card-price-main")
    if not main:return None,None
    d=main.select_one(".ka-card-dollars")
    c=main.select_one(".ka-card-cents")
    if not d:return None,None
    try:
        ds=re.sub(r"[^0-9]","",d.get_text(" ",strip=True))
        cs=re.sub(r"[^0-9]","",c.get_text(" ",strip=True)) if c else "00"
        if not ds:return None,None
        return float(ds+"."+((cs+"00")[:2])),"ka-card-price-main"
    except Exception:return None,None

def search_kickass(query,limit=30,timeout=25):
    r=requests.get(SEARCH.format(q=quote_plus(query)),headers={
        "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/153 Safari/537.36",
        "Accept":"text/html,application/xhtml+xml",
    },timeout=timeout,allow_redirects=True)
    if r.status_code!=200: raise KickAssUnavailable(f"KickAss HTTP {r.status_code}")
    soup=BeautifulSoup(r.text,"html.parser")
    cards=soup.select(".product-card")
    # A captcha word in Shopify scripts is not a block if normal cards exist.
    if not cards:
        low=r.text.lower()
        if "captcha" in low or "access denied" in low:
            raise KickAssUnavailable("KickAss did not return normal product-card structure.")
        raise KickAssNoResults("KickAss search completed but returned no product cards.")
    out=[]; seen=set()
    for card in cards:
        a=card.select_one("a.product-card-title[href*='/products/']") or card.select_one("a[href*='/products/']")
        if not a:continue
        title=" ".join(a.get_text(" ",strip=True).split()) or (a.get("title") or "").strip()
        href=a.get("href")
        if not title or not href:continue
        url=urljoin(BASE,href.split("?",1)[0])
        if url in seen:continue
        seen.add(url)
        price,source=_card_price(card)
        badge=" ".join(x.get_text(" ",strip=True) for x in card.select(".product-card--badges,.badge,.featured-banner-text"))
        text=" ".join(card.get_text(" ",strip=True).split())
        low=(title+" "+badge).lower()
        bundle=("bundle" in low or "bundle deal" in low)
        out.append({"retailer":"KickAss Products","title":unescape(title),"url":url,
                    "price":price,"price_source":source,"bundle":bundle,
                    "badge_text":badge,"raw_text":text})
        if len(out)>=limit:break
    if not out: raise KickAssNoResults("KickAss search completed but returned no usable product records.")
    return out
