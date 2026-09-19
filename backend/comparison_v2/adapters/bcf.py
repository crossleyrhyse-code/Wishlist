from __future__ import annotations

import json
import re
from html import unescape
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import quote_plus, urljoin
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from ..core.retailer_product import RetailerProduct

BASE = "https://www.bcf.com.au"
SEARCH = BASE + "/search?q={query}"
USER_AGENT = "Mozilla/5.0 (compatible; WishlistPriceComparison/0.1; local-development)"


class BCFUnavailable(RuntimeError):
    pass


class _JSONLDParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_jsonld = False
        self.parts = []
        self.blocks = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "script":
            return
        a = {k.lower(): (v or "") for k, v in attrs}
        if "ld+json" in a.get("type", "").lower():
            self.in_jsonld = True
            self.parts = []

    def handle_data(self, data):
        if self.in_jsonld:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self.in_jsonld:
            self.blocks.append("".join(self.parts))
            self.in_jsonld = False
            self.parts = []


def _money(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)", str(value))
    return float(m.group(1).replace(",", "")) if m else None


def _iter_json(obj) -> Iterable[dict]:
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from _iter_json(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _iter_json(v)


def _normal_price_from_offer(offers):
    """Return the ordinary advertised price. Do not silently use Club BCF/member price."""
    if isinstance(offers, list):
        offers = offers[0] if offers else None
    if not isinstance(offers, dict):
        return None
    return _money(offers.get("price") or offers.get("lowPrice"))


def _jsonld_products(html, limit):
    parser = _JSONLDParser()
    parser.feed(html)
    out = []
    seen = set()
    for block in parser.blocks:
        try:
            data = json.loads(block)
        except Exception:
            continue
        for node in _iter_json(data):
            typ = node.get("@type")
            types = typ if isinstance(typ, list) else [typ]
            if "Product" not in types:
                continue
            title = str(node.get("name") or "").strip()
            url = str(node.get("url") or "").strip()
            if not title or not url:
                continue
            url = urljoin(BASE, url)
            key = (title.lower(), url)
            if key in seen:
                continue
            seen.add(key)
            price = _normal_price_from_offer(node.get("offers"))
            out.append(RetailerProduct(
                retailer="BCF",
                title=unescape(title),
                url=url,
                price=price,
                price_text=(f"${price:.2f}" if price is not None else None),
            ))
            if len(out) >= limit:
                return out
    return out


def _fallback_products(html, limit):
    """
    Conservative fallback for BCF product tiles.
    Requires a BCF product URL ending in /<digits>.html and looks only at a
    small surrounding tile-sized region for a title and ordinary dollar price.
    """
    out = []
    seen = set()
    link_re = re.compile(
        r'<a\b[^>]*href=["\']([^"\']+/\d+\.html(?:\?[^"\']*)?)["\'][^>]*>(.*?)</a>',
        re.I | re.S,
    )
    for m in link_re.finditer(html):
        href, body = m.group(1), m.group(2)
        title = re.sub(r"<[^>]+>", " ", body)
        title = unescape(re.sub(r"\s+", " ", title)).strip()
        if len(title) < 4:
            # Product name is sometimes adjacent to the image/link.
            window = html[m.end():m.end()+1800]
            candidates = re.findall(r'(?:product-name|productName|product-title)[^>]*>\s*(?:<[^>]+>\s*)*([^<]{4,180})', window, re.I)
            title = unescape(candidates[0]).strip() if candidates else ""
        if not title:
            continue
        url = urljoin(BASE, href)
        key = url.split("?")[0]
        if key in seen:
            continue

        # Price near the same product tile. We intentionally take the first
        # ordinary displayed price; Club/member pricing is not substituted.
        window = html[max(0, m.start()-400):m.end()+2200]
        prices = re.findall(r'\$\s*([0-9][0-9,]*(?:\.[0-9]{2})?)', window)
        price = _money(prices[0]) if prices else None
        seen.add(key)
        out.append(RetailerProduct(
            retailer="BCF",
            title=title,
            url=url,
            price=price,
            price_text=(f"${price:.2f}" if price is not None else None),
        ))
        if len(out) >= limit:
            break
    return out


def search_bcf(query: str, limit: int = 30):
    query = str(query or "").strip()
    if not query:
        return []
    url = SEARCH.format(query=quote_plus(query))
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-AU,en;q=0.9",
    })
    try:
        with urlopen(req, timeout=20) as response:
            status = getattr(response, "status", 200)
            html = response.read().decode("utf-8", errors="replace")
    except HTTPError as e:
        raise BCFUnavailable(f"BCF unavailable (HTTP {e.code}).") from None
    except (URLError, TimeoutError, OSError) as e:
        raise BCFUnavailable(f"BCF unavailable ({type(e).__name__}).") from None

    low = html.lower()
    if status >= 400 or "request could not be satisfied" in low or "access denied" in low:
        raise BCFUnavailable("BCF search is currently unavailable.")
    if "no products were found for your search" in low:
        return []

    products = _jsonld_products(html, limit)
    if not products:
        products = _fallback_products(html, limit)
    if not products:
        raise BCFUnavailable("BCF returned no supported product records.")
    return products[:limit]
