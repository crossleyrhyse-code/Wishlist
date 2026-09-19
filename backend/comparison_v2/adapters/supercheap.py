from __future__ import annotations

import re
from html import unescape
from urllib.parse import quote, urljoin
from urllib.request import Request, urlopen

from ..core.retailer_product import RetailerProduct

BASE = "https://www.supercheapauto.com.au"
SEARCH = BASE + "/search?q={query}&searchtype=product"
UA = "Mozilla/5.0 (compatible; WishlistPriceComparison/0.1; local-development)"


class SupercheapUnavailable(RuntimeError):
    pass


def _money(value):
    if value is None:
        return None
    try:
        text = str(value).replace(",", "")
        match = re.search(r"([0-9]+(?:\.[0-9]{1,2})?)", text)
        return float(match.group(1)) if match else None
    except (TypeError, ValueError):
        return None


def _clean_text(value):
    value = re.sub(r"<[^>]+>", " ", value or "")
    return unescape(re.sub(r"\s+", " ", value)).strip()


def _normal_url(value):
    if not value:
        return None
    return urljoin(BASE, unescape(str(value).strip()))


def _class_block(tile, class_name):
    # Supercheap's search response is server-rendered. We only inspect the
    # named pricing element inside this one product tile.
    pattern = (
        r'<(?:span|div)\b[^>]*class=["\'][^"\']*\b'
        + re.escape(class_name)
        + r'\b[^"\']*["\'][^>]*>(.*?)</(?:span|div)\s*>'
    )
    match = re.search(pattern, tile, re.I | re.S)
    return match.group(1) if match else None


def _extract_price(tile):
    # Public advertised sale/current price wins when present.
    sale = _class_block(tile, "product-sales-price")
    price = _money(_clean_text(sale)) if sale else None
    if price is not None:
        return price

    # Otherwise use the ordinary public standard price.
    standard = _class_block(tile, "product-standard-price")
    price = _money(_clean_text(standard)) if standard else None
    if price is not None:
        return price

    # Deliberately do not substitute member/loyalty pricing.
    return None


def _extract_title_url(tile):
    # Prefer the product-name link seen in the live Supercheap response.
    block = _class_block(tile, "product-name") or tile
    m = re.search(
        r'<a\b[^>]*class=["\'][^"\']*\bname-link\b[^"\']*["\'][^>]*'
        r'href=["\']([^"\']+)["\'][^>]*>(.*?)</a\s*>',
        block,
        re.I | re.S,
    )
    if not m:
        # Attribute order can change, so use a conservative /p/...html fallback
        # inside the same product tile.
        m = re.search(
            r'<a\b[^>]*href=["\']([^"\']*/p/[^"\']+\.html(?:\?[^"\']*)?)["\'][^>]*>(.*?)</a\s*>',
            block,
            re.I | re.S,
        )
    if not m:
        return None, None

    url = _normal_url(m.group(1))
    title = _clean_text(m.group(2))

    # Some links use image-only content. Fall back to title attribute.
    if not title:
        open_tag = m.group(0).split(">", 1)[0]
        tm = re.search(r'title=["\'](?:Go to Product:\s*)?([^"\']+)["\']', open_tag, re.I)
        if tm:
            title = unescape(tm.group(1)).strip()

    if not title or not url:
        return None, None
    return title, url


def _product_tiles(html):
    # Live response uses:
    #   <li class="grid-tile"> ... <div class="product-tile"> ... </li>
    # Splitting on grid tiles avoids trying to parse arbitrary nested divs.
    starts = list(
        re.finditer(
            r'<li\b[^>]*class=["\'][^"\']*\bgrid-tile\b[^"\']*["\'][^>]*>',
            html,
            re.I,
        )
    )
    for i, start in enumerate(starts):
        end = starts[i + 1].start() if i + 1 < len(starts) else len(html)
        tile = html[start.start():end]
        if "product-tile" in tile.lower():
            yield tile


def _parse_search_html(html):
    products = []
    seen = set()

    for tile in _product_tiles(html):
        title, url = _extract_title_url(tile)
        if not title or not url:
            continue

        key = url.split("?", 1)[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)

        price = _extract_price(tile)
        products.append(
            RetailerProduct(
                retailer="Supercheap Auto",
                title=title,
                url=url,
                price=price,
                price_text=f"${price:.2f}" if price is not None else None,
            )
        )

    return products



def _fallback_queries(query):
    """Conservative fallback searches used only after the supplied query returns no products."""
    text = re.sub(r"\s+", " ", str(query or "")).strip()
    low = text.lower()
    fallbacks = []

    # Real live failure: a long Kings 270 awning title returned no Supercheap
    # tiles, while Supercheap has relevant 270-degree awnings. Keep the useful
    # category/specification and drop retailer-specific marketing words.
    if re.search(r"\bawning\b", low):
        angle = re.search(r"\b(180|270|360)\s*(?:°|deg(?:ree)?s?)?\b", low)
        if angle:
            fallbacks.append(f"{angle.group(1)} awning")
        fallbacks.append("awning")

    # Preserve order and avoid retrying the exact same query.
    seen = {low}
    result = []
    for item in fallbacks:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _fetch_search_html(query):
    url = SEARCH.format(query=quote(query))
    request = Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8", "replace")
    except Exception as exc:
        raise SupercheapUnavailable(
            f"Supercheap Auto request failed: {exc}"
        ) from exc


def _blocked_without_results(html):
    lowered = html.lower()
    has_product_results = (
        "grid-tile" in lowered
        and "product-tile" in lowered
        and "/p/" in lowered
    )
    return not has_product_results and (
        "access denied" in lowered
        or "request could not be satisfied" in lowered
        or "captcha" in lowered
    )


def search_supercheap(query, limit=30):
    attempts = [str(query or "").strip(), *_fallback_queries(query)]

    for attempt in attempts:
        html = _fetch_search_html(attempt)

        # A genuine block should stop immediately. A normal zero-result page,
        # however, is allowed to fall through to the conservative retry.
        if _blocked_without_results(html):
            raise SupercheapUnavailable(
                "Supercheap Auto search is currently unavailable"
            )

        products = _parse_search_html(html)
        if products:
            return products[:limit]

    raise SupercheapUnavailable(
        "Supercheap Auto returned no parseable product results"
    )
