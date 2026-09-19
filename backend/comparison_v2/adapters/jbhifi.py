from __future__ import annotations

from urllib.parse import parse_qs, quote_plus, urlencode, urlparse

from ..core.retailer_product import RetailerProduct

SEARCH_PAGE = "https://www.jbhifi.com.au/search?query={query}"


class JBHiFiUnavailable(RuntimeError):
    pass


class JBHiFiNoResults(RuntimeError):
    pass


def _money(value):
    try:
        if value is None or value == "":
            return None
        if isinstance(value, (int, float)):
            return float(value)
        import re

        m = re.search(r"\d+(?:,\d{3})*(?:\.\d{1,2})?", str(value).replace("$", ""))
        return float(m.group(0).replace(",", "")) if m else None
    except (TypeError, ValueError):
        return None


def _normalise_hit(hit):
    if not isinstance(hit, dict):
        return None

    title = str(hit.get("title") or hit.get("name") or "").strip()
    handle = str(hit.get("handle") or "").strip().strip("/")
    url = str(hit.get("url") or "").strip()

    if not url and handle:
        url = f"https://www.jbhifi.com.au/products/{handle}"
    if url.startswith("/"):
        url = "https://www.jbhifi.com.au" + url
    if not title or not url:
        return None

    price = _money(hit.get("price"))
    return {
        "product": RetailerProduct(
            "JB Hi-Fi",
            title,
            url,
            price,
            f"${price:.2f}" if price is not None else None,
        ),
        "sku": str(hit.get("sku") or hit.get("objectID") or "").strip(),
        "vendor": str(hit.get("vendor") or "").strip(),
        "product_type": str(hit.get("product_type") or "").strip(),
        "bundle": False,
    }


def _algolia_config_from_url(url):
    """Extract JB's current public Algolia search configuration from a browser request."""
    try:
        parsed = urlparse(url)
        if "algolia.net" not in parsed.netloc.lower():
            return None

        marker = "/1/indexes/"
        if marker not in parsed.path:
            return None

        tail = parsed.path.split(marker, 1)[1]
        index_name = tail.split("/", 1)[0]
        if not index_name or index_name == "*":
            return None

        qs = parse_qs(parsed.query)
        app_id = (qs.get("x-algolia-application-id") or [""])[0]
        api_key = (qs.get("x-algolia-api-key") or [""])[0]
        agent = (qs.get("x-algolia-agent") or [""])[0]
        if not app_id or not api_key:
            return None

        return {
            "host": parsed.netloc,
            "index_name": index_name,
            "app_id": app_id,
            "api_key": api_key,
            "agent": agent,
        }
    except Exception:
        return None


def _search_algolia(config, query, limit, timeout):
    """
    Use the public Algolia configuration exposed by the current JB browser session.

    Nothing is hard-coded: the application id, public search key, host and index are
    all captured fresh from JB's own ordinary storefront request.
    """
    try:
        import requests
    except Exception as exc:
        raise JBHiFiUnavailable("requests is required for JB Hi-Fi search.") from exc

    params = {
        "x-algolia-application-id": config["app_id"],
        "x-algolia-api-key": config["api_key"],
    }
    if config.get("agent"):
        params["x-algolia-agent"] = config["agent"]

    endpoint = f'https://{config["host"]}/1/indexes/*/queries?{urlencode(params)}'
    hits_per_page = max(20, min(int(limit or 20) * 3, 100))
    body = {
        "requests": [
            {
                "indexName": config["index_name"],
                "params": urlencode(
                    {
                        "query": query,
                        "hitsPerPage": hits_per_page,
                        "page": 0,
                    }
                ),
            }
        ]
    }

    try:
        resp = requests.post(endpoint, json=body, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        raise JBHiFiUnavailable(f"JB Hi-Fi structured search request failed: {exc}") from exc

    records = []
    for result in data.get("results", []):
        for hit in result.get("hits", []):
            if isinstance(hit, dict) and (hit.get("title") or hit.get("name")):
                records.append(hit)
    return records


def search_jbhifi(query, limit=20, timeout=30):
    query = " ".join(str(query or "").split()).strip()
    if not query:
        raise ValueError("query is required")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:
        raise JBHiFiUnavailable("Playwright/Chromium is required for JB Hi-Fi search.") from exc

    page_url = SEARCH_PAGE.format(query=quote_plus(query))
    records = []
    algolia_config = None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1400, "height": 1000})

            def request(req):
                nonlocal algolia_config
                low = req.url.lower()

                # Capture JB's current public Algolia configuration from the
                # outgoing browse request. This fires immediately and avoids a
                # response-callback timing race on Google's A/B search branch.
                if algolia_config is None and "algolia.net/" in low and "/1/indexes/" in low:
                    cfg = _algolia_config_from_url(req.url)
                    if cfg:
                        algolia_config = cfg

            def response(resp):
                low = resp.url.lower()

                # If this session happens to use the Algolia UI branch, use the
                # search response directly and avoid the fallback request entirely.
                if "algolia.net/" not in low or "/queries" not in low or resp.status != 200:
                    return
                try:
                    data = resp.json()
                    for result in data.get("results", []):
                        for hit in result.get("hits", []):
                            if isinstance(hit, dict) and (hit.get("title") or hit.get("name")):
                                records.append(hit)
                except Exception:
                    pass

            page.on("request", request)
            page.on("response", response)
            page.goto(page_url, wait_until="domcontentloaded", timeout=timeout * 1000)
            page.wait_for_timeout(6500)
            page.close()
            browser.close()
    except Exception as exc:
        raise JBHiFiUnavailable(f"JB Hi-Fi browser search failed: {exc}") from exc

    # Google A/B branch: the page did not issue a product query, but JB still
    # exposed its current public Algolia config through the normal browse request.
    # Use that fresh config once rather than retrying browser sessions at random.
    if not records:
        if not algolia_config:
            raise JBHiFiUnavailable(
                "JB Hi-Fi did not expose a usable structured search configuration in this session."
            )
        records = _search_algolia(algolia_config, query, limit, timeout)

    unique = []
    seen = set()
    for hit in records:
        row = _normalise_hit(hit)
        if not row:
            continue
        product = row["product"]
        key = row["sku"].lower() or product.url.split("?", 1)[0].rstrip("/").lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)
        if len(unique) >= limit:
            break

    if not unique:
        raise JBHiFiNoResults("JB Hi-Fi structured search completed successfully but found no usable products.")

    return unique
