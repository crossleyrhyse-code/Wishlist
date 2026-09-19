# ============================================================
# IMPORTS
# ============================================================

# Regular expressions.
# Used for cleaning product names and finding model information.
import re
import time

# Built into Python.
# Gives us a general text-similarity score between two strings.
from difflib import SequenceMatcher

# Converts normal search text into something safe to place
# inside a website search URL.
from urllib.parse import quote_plus

# Selenium tools used to find products on retailer search pages.
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Reuse the same Chrome setup Wishlist already uses
# for normal product price checks.
from price_checker import create_price_driver, get_product_price

# Pull the saved BCF price selector from the same store profile
# used by the rest of Wishlist.
from store_manager import get_price_selector


# ============================================================
# GENERIC PRODUCT WORDS
# ============================================================

GENERIC_PRODUCT_WORDS = {
    "a",
    "an",
    "and",
    "the",
    "for",
    "with",
    "compact",
    "spin",
    "spinning",
    "reel",
    "reels",
    "model",
    "series"
}


# ============================================================
# NORMALIZE PRODUCT NAME
# ============================================================

def normalize_product_name(name):
    """
    Clean a product name before comparing it.
    """

    name = name.lower()

    name = re.sub(
        r"[^a-z0-9]+",
        " ",
        name
    )

    name = re.sub(
        r"([0-9])([a-z])",
        r"\1 \2",
        name
    )

    name = re.sub(
        r"([a-z])([0-9])",
        r"\1 \2",
        name
    )

    name = re.sub(
        r"\bxgfd\b",
        "xg fd",
        name
    )

    name = re.sub(
        r"\bhgfd\b",
        "hg fd",
        name
    )

    name = " ".join(
        name.split()
    )

    return name


# ============================================================
# GET IMPORTANT NUMBERS
# ============================================================

def get_important_numbers(name):
    """
    Pull numeric identifiers from a product name.
    """

    normalized_name = normalize_product_name(
        name
    )

    numbers = re.findall(
        r"\b\d+\b",
        normalized_name
    )

    return numbers


# ============================================================
# GET ALL PRODUCT WORDS
# ============================================================

def get_product_words(name):
    """
    Return every word/token contained in a cleaned product name.
    """

    normalized_name = normalize_product_name(
        name
    )

    return set(
        normalized_name.split()
    )


# ============================================================
# GET IDENTITY WORDS
# ============================================================

def get_identity_words(name):
    """
    Return words that are more useful for identifying the actual
    product.
    """

    words = get_product_words(
        name
    )

    identity_words = {
        word
        for word in words
        if word not in GENERIC_PRODUCT_WORDS
    }

    return identity_words


# ============================================================
# GET BRAND
# ============================================================

def get_brand(name):
    """
    Basic first-pass brand detection.

    For now we assume the first meaningful word in a retailer's
    product title is the brand.
    """

    normalized_name = normalize_product_name(
        name
    )

    words = normalized_name.split()

    if not words:
        return None

    return words[0]


# ============================================================
# CALCULATE NORMAL NAME SIMILARITY
# ============================================================

def calculate_name_similarity(name_a, name_b):
    """
    Calculate general text similarity between two product names.
    """

    normalized_a = normalize_product_name(
        name_a
    )

    normalized_b = normalize_product_name(
        name_b
    )

    sequence_score = SequenceMatcher(
        None,
        normalized_a,
        normalized_b
    ).ratio()

    words_a = get_product_words(
        name_a
    )

    words_b = get_product_words(
        name_b
    )

    if words_a or words_b:

        shared_words = words_a.intersection(
            words_b
        )

        word_score = (
            len(shared_words)
            /
            max(
                len(words_a),
                len(words_b)
            )
        )

    else:
        word_score = 0.0

    final_score = (
        sequence_score * 0.6
        +
        word_score * 0.4
    )

    return final_score


# ============================================================
# CALCULATE IDENTITY SIMILARITY
# ============================================================

def calculate_identity_similarity(name_a, name_b):
    """
    Compare only the more important identifying words.
    """

    identity_a = get_identity_words(
        name_a
    )

    identity_b = get_identity_words(
        name_b
    )

    if not identity_a or not identity_b:
        return 0.0

    shared_identity = identity_a.intersection(
        identity_b
    )

    identity_score = (
        len(shared_identity)
        /
        min(
            len(identity_a),
            len(identity_b)
        )
    )

    return identity_score


# ============================================================
# CHECK IMPORTANT NUMBERS
# ============================================================

def important_numbers_match(name_a, name_b):
    """
    Check whether numeric identifiers agree.
    """

    numbers_a = set(
        get_important_numbers(
            name_a
        )
    )

    numbers_b = set(
        get_important_numbers(
            name_b
        )
    )

    if not numbers_a or not numbers_b:
        return True

    return bool(
        numbers_a.intersection(
            numbers_b
        )
    )


# ============================================================
# CHECK BRAND MATCH
# ============================================================

def brands_match(name_a, name_b):
    """
    Check whether both product titles appear to use the same brand.
    """

    brand_a = get_brand(
        name_a
    )

    brand_b = get_brand(
        name_b
    )

    if not brand_a or not brand_b:
        return True

    return brand_a == brand_b


# ============================================================
# CLASSIFY PRODUCT MATCH
# ============================================================

PRODUCT_TYPE_ALIASES = {
    "chainsaw": ("chainsaw", "chain saw"),
    "awning": ("awning",),
    "chair": ("chair",),
    "mower": ("mower", "lawn mower"),
    "fridge": ("fridge", "refrigerator"),
    "freezer": ("freezer",),
    "tent": ("tent",),
    "generator": ("generator",),
    "compressor": ("compressor",),
    "drill": ("drill",),
    "grinder": ("grinder",),
    "blower": ("blower",),
    "saw": ("circular saw", "mitre saw", "miter saw", "reciprocating saw"),
}

ACCESSORY_WORDS = {
    "bracket", "brackets", "wall", "walls", "extension", "extensions",
    "cover", "covers", "bag", "bags", "mount", "mounting", "holder",
    "holders", "replacement", "spare", "adapter", "adaptor", "stand",
    "pole", "poles", "strap", "straps", "mesh", "sidewall", "sidewalls",
}


def detect_product_type(name):
    """Return a broad product identity used for discovery and guardrails."""
    normalized = normalize_product_name(name)
    padded = f" {normalized} "

    # Prefer specific multi-word/product identities before generic "saw".
    for product_type, aliases in PRODUCT_TYPE_ALIASES.items():
        for alias in aliases:
            alias_norm = normalize_product_name(alias)
            if f" {alias_norm} " in padded:
                return product_type
    return None


def _accessory_conflict(tracked_name, candidate_name):
    """Reject obvious accessories when the tracked item is the main product."""
    tracked_words = get_product_words(tracked_name)
    candidate_words = get_product_words(candidate_name)
    candidate_accessories = candidate_words.intersection(ACCESSORY_WORDS)
    tracked_accessories = tracked_words.intersection(ACCESSORY_WORDS)
    return bool(candidate_accessories and not tracked_accessories)



def get_model_tokens(name):
    """Extract likely manufacturer model codes such as DUC254Z."""
    compact = re.sub(r"[^a-z0-9]+", "", str(name).lower())
    return set(re.findall(r"[a-z]{2,}\d+[a-z0-9]*", compact))

def model_relationship(name_a, name_b):
    a, b = get_model_tokens(name_a), get_model_tokens(name_b)
    if not a or not b:
        return "UNKNOWN"
    return "SAME" if a.intersection(b) else "DIFFERENT"

def classify_product_match(
    name_a,
    name_b,
    exact_threshold=0.80,
    similar_threshold=0.50,
    possible_threshold=0.35,
    identity_threshold=0.75
):
    """Classify a candidate while protecting the core product identity."""
    name_score = calculate_name_similarity(name_a, name_b)
    identity_score = calculate_identity_similarity(name_a, name_b)
    number_match = important_numbers_match(name_a, name_b)
    brand_match = brands_match(name_a, name_b)

    tracked_type = detect_product_type(name_a)
    candidate_type = detect_product_type(name_b)
    type_match = not tracked_type or tracked_type == candidate_type
    accessory_conflict = _accessory_conflict(name_a, name_b)
    model_match = model_relationship(name_a, name_b)

    # A bracket/wall/cover for an awning is not an awning. Likewise, when we
    # know both product types and they differ, similarity words must not win.
    if accessory_conflict or not type_match:
        match_type = "NO MATCH"
        display_score = min(max(name_score, identity_score), 0.34)
    else:
        normal_exact_match = (
            name_score >= exact_threshold and number_match and brand_match and model_match != "DIFFERENT"
        )
        identity_exact_match = (
            identity_score >= identity_threshold and number_match and brand_match and model_match != "DIFFERENT"
        )

        if normal_exact_match or identity_exact_match:
            match_type = "EXACT MATCH"
        elif model_match == "DIFFERENT" and type_match:
            match_type = "SIMILAR PRODUCT"
        elif name_score >= similar_threshold or identity_score >= similar_threshold:
            match_type = "SIMILAR PRODUCT"
        elif name_score >= possible_threshold or identity_score >= possible_threshold:
            match_type = "POSSIBLE MATCH"
        else:
            match_type = "NO MATCH"
        display_score = max(name_score, identity_score)

    return {
        "score": display_score,
        "percentage": round(display_score * 100),
        "name_score": round(name_score * 100),
        "identity_score": round(identity_score * 100),
        "numbers_match": number_match,
        "brand_match": brand_match,
        "product_type_match": type_match,
        "accessory_conflict": accessory_conflict,
        "match_type": match_type,
    }


def build_search_terms(product_name):
    """Build a broad shopping-intent query, not a copy of the retailer title.

    Examples:
      Kings 270 Awning -> 270 awning
      Makita 18V 250mm Brushless Chainsaw DUC254Z -> 18v chainsaw
      Chair -> chair

    Brand/model/detail words remain available to the scorer after discovery.
    """
    normalized = normalize_product_name(product_name)
    product_type = detect_product_type(product_name)

    if product_type:
        specs = []

        # Voltage is a useful broad class for cordless power tools.
        voltage = re.search(r"\b(\d{1,3})\s*v\b", normalized)
        if voltage:
            specs.append(f"{voltage.group(1)}v")

        # For wrap-around awnings, the angle defines the product class.
        if product_type == "awning":
            angle = re.search(r"\b(180|270|360)\b", normalized)
            if angle:
                specs.append(angle.group(1))

        return " ".join(specs + [product_type]).strip()

    # Unknown product category: keep the old safe fallback, but strip generic
    # filler words rather than guessing at what the product is.
    words = [
        word for word in normalized.split()
        if word not in GENERIC_PRODUCT_WORDS
    ]
    return " ".join(words)


# ============================================================
# SEARCH BCF
# ============================================================

def search_bcf(product_name):
    """Search BCF with resilient page handling and useful diagnostics."""
    search_text = build_search_terms(product_name)
    encoded_search = quote_plus(search_text)
    search_url = "https://www.bcf.com.au/search?q=" + encoded_search

    print()
    print("=" * 60)
    print("SEARCHING BCF")
    print("=" * 60)
    print(f"Search Text: {search_text}")
    print(f"Search URL: {search_url}")
    print()

    driver = None
    stage = "creating Chrome driver"
    try:
        driver = create_price_driver()

        stage = "opening BCF search page"
        driver.get(search_url)

        stage = "waiting for BCF document"
        WebDriverWait(driver, 15).until(
            lambda d: d.execute_script("return document.readyState") in {"interactive", "complete"}
        )

        # BCF can hydrate its product grid after document.readyState completes.
        # A short settle is more robust than waiting for one retailer CSS class.
        stage = "allowing BCF results to render"
        time.sleep(4)

        current_url = driver.current_url or ""
        page_title = driver.title or ""
        body_text = ""
        try:
            body_text = (driver.find_element(By.TAG_NAME, "body").text or "")[:3000]
        except Exception:
            pass

        print(f"BCF page title: {page_title}")
        print(f"BCF final URL: {current_url}")

        blocked_text = (page_title + " " + body_text).lower()
        blocked_markers = (
            "403 forbidden", "access denied", "request blocked",
            "captcha", "verify you are human", "robot or human",
        )
        if any(marker in blocked_text for marker in blocked_markers):
            raise RuntimeError("BCF blocked the automated search page")

        stage = "reading BCF links"
        raw_links = driver.execute_script(
            """
            return Array.from(document.querySelectorAll('a[href]')).map(function(link) {
                return {
                    url: link.href || '',
                    title: (link.getAttribute('aria-label') || link.getAttribute('title') ||
                            link.innerText || link.textContent || '').trim()
                };
            });
            """
        ) or []
        print(f"BCF links visible: {len(raw_links)}")

        results = []
        seen_urls = set()
        for item in raw_links:
            url = (item.get("url") or "").strip()
            title = (item.get("title") or "").strip()
            lower_url = url.lower()
            if not url or not title or len(title) < 4 or url in seen_urls:
                continue
            if "bcf.com.au" not in lower_url:
                continue
            # Current BCF product URLs look like /p/name/123456.html.
            if "/p/" not in lower_url or not lower_url.endswith(".html"):
                continue
            seen_urls.add(url)
            results.append({"name": title, "url": url, "price": extract_price_from_text(title)})

        print(f"BCF candidates collected: {len(results)}")

        # Zero real product links is different from a valid zero-match result:
        # it usually means BCF changed/blocked its rendered search page.
        if not results:
            snippet = " ".join(body_text.split())[:350]
            print(f"BCF body preview: {snippet}")
            raise RuntimeError("BCF search page loaded but no product links were readable")

        return results

    except Exception as error:
        print()
        print("BCF SEARCH FAILED")
        print(f"Stage: {stage}")
        print(f"Type: {type(error).__name__}")
        print(f"Reason: {repr(error)}")
        raise RuntimeError(
            f"BCF search unavailable during {stage}: {type(error).__name__}"
        ) from error
    finally:
        if driver is not None:
            driver.quit()


# ============================================================
# SCORE SEARCH RESULTS
# ============================================================

def score_search_results(tracked_product_name, search_results):
    """
    Run every retailer search result through our product matcher.

    Each result receives its match score and classification, then
    the results are sorted with the strongest matches first.
    """

    scored_results = []

    for result in search_results:

        match_result = classify_product_match(
            tracked_product_name,
            result["name"]
        )

        scored_result = {
            "name": result["name"],
            "url": result["url"],
            "percentage": match_result["percentage"],
            "name_score": match_result["name_score"],
            "identity_score": match_result["identity_score"],
            "numbers_match": match_result["numbers_match"],
            "brand_match": match_result["brand_match"],
            "match_type": match_result["match_type"],
            "price": result.get("price"),
        }

        scored_results.append(
            scored_result
        )

    # Exact products first, then similar, possible, then no matches.
    match_priority = {
        "EXACT MATCH": 4,
        "SIMILAR PRODUCT": 3,
        "POSSIBLE MATCH": 2,
        "NO MATCH": 1
    }

    scored_results.sort(
        key=lambda item: (
            match_priority.get(
                item["match_type"],
                0
            ),
            item["percentage"]
        ),
        reverse=True
    )

    return scored_results


# ============================================================
# GET BEST EXACT MATCH
# ============================================================

def get_best_exact_match(scored_results):
    """
    Return the strongest EXACT MATCH from a scored result list.

    The list is already sorted with the strongest matches first,
    so the first exact result is our best candidate.

    If no exact product was found, return None.
    """

    for result in scored_results:

        if result["match_type"] == "EXACT MATCH":
            return result

    return None


# ============================================================
# CHECK BCF EXACT-MATCH PRICE
# ============================================================

def get_bcf_exact_match_price(exact_match):
    """
    Retrieve the live BCF price for an exact product match.

    This deliberately happens AFTER matching.

    We do not want to open every BCF product page just to discover
    that most of them are only Similar Products or No Matches.
    """

    if exact_match is None:
        return None

    # Reuse the selector already stored in store_manager.py.
    bcf_price_selector = get_price_selector(
        "BCF"
    )

    # get_product_price() only needs a URL and price selector.
    temporary_product = {
        "url": exact_match["url"],
        "price_selector": bcf_price_selector
    }

    live_price = get_product_price(
        temporary_product
    )

    return live_price


# ============================================================
# TEST AREA
# ============================================================

if __name__ == "__main__":

    # --------------------------------------------------------
    # TEST 1 - REAL ANACONDA / BCF PRODUCT
    # --------------------------------------------------------

    tracked_product = (
        "Shimano Nasci Compact 5000XGFD Spin Reel"
    )

    comparison_product = (
        "Shimano Nasci FD 5000C XG Spinning Reel"
    )

    result = classify_product_match(
        tracked_product,
        comparison_product
    )

    print()
    print("=" * 60)
    print("WISHLIST PRODUCT COMPARISON TEST")
    print("=" * 60)

    print()
    print("TRACKED PRODUCT:")
    print(tracked_product)

    print()
    print("COMPARISON PRODUCT:")
    print(comparison_product)

    print()
    print("-" * 60)

    print(
        f"Normal Name Score: "
        f"{result['name_score']}%"
    )

    print(
        f"Identity Score: "
        f"{result['identity_score']}%"
    )

    print(
        f"Displayed Match Score: "
        f"{result['percentage']}%"
    )

    print(
        f"Brand Match: "
        f"{result['brand_match']}"
    )

    print(
        f"Numbers Match: "
        f"{result['numbers_match']}"
    )

    print(
        f"Result: "
        f"{result['match_type']}"
    )

    print("-" * 60)

    # --------------------------------------------------------
    # TEST 2 - WRONG SIZE / MODEL
    # --------------------------------------------------------

    wrong_product = (
        "Shimano Nasci FD 3000C XG Spinning Reel"
    )

    wrong_result = classify_product_match(
        tracked_product,
        wrong_product
    )

    print()
    print("=" * 60)
    print("WRONG MODEL SAFETY TEST")
    print("=" * 60)

    print()
    print("TRACKED PRODUCT:")
    print(tracked_product)

    print()
    print("COMPARISON PRODUCT:")
    print(wrong_product)

    print()
    print("-" * 60)

    print(
        f"Normal Name Score: "
        f"{wrong_result['name_score']}%"
    )

    print(
        f"Identity Score: "
        f"{wrong_result['identity_score']}%"
    )

    print(
        f"Brand Match: "
        f"{wrong_result['brand_match']}"
    )

    print(
        f"Numbers Match: "
        f"{wrong_result['numbers_match']}"
    )

    print(
        f"Result: "
        f"{wrong_result['match_type']}"
    )

    print("-" * 60)

    # --------------------------------------------------------
    # TEST 3 - SEARCH AND SCORE BCF
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BCF SEARCH + MATCH TEST")
    print("=" * 60)

    bcf_results = search_bcf(
        tracked_product
    )

    scored_bcf_results = score_search_results(
        tracked_product,
        bcf_results
    )

    print()
    print(
        f"Products Found: "
        f"{len(scored_bcf_results)}"
    )

    print()

    # Print every result while testing.
    # Seeing the weaker matches helps us tune the matcher.
    for result in scored_bcf_results:

        print(
            f"{result['percentage']}% - "
            f"{result['match_type']}"
        )

        print(
            result["name"]
        )

        print(
            f"Name Score: "
            f"{result['name_score']}%"
        )

        print(
            f"Identity Score: "
            f"{result['identity_score']}%"
        )

        print(
            f"Brand Match: "
            f"{result['brand_match']}"
        )

        print(
            f"Numbers Match: "
            f"{result['numbers_match']}"
        )

        print(
            result["url"]
        )

        print("-" * 60)

    # --------------------------------------------------------
    # TEST 4 - GET PRICE FOR BEST EXACT MATCH
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("BCF EXACT-MATCH PRICE TEST")
    print("=" * 60)

    best_exact_match = get_best_exact_match(
        scored_bcf_results
    )

    if best_exact_match is None:

        print()
        print("No exact BCF product match was found.")

    else:

        print()
        print("BEST EXACT MATCH:")
        print(
            best_exact_match["name"]
        )

        print(
            best_exact_match["url"]
        )

        print()
        print("Checking live BCF price...")

        try:

            exact_match_price = get_bcf_exact_match_price(
                best_exact_match
            )

            print()
            print(
                f"BCF Price: "
                f"${exact_match_price:,.2f}"
            )

        except Exception as error:

            print()
            print("BCF PRICE CHECK FAILED")

            print(
                f"Reason: "
                f"{error}"
            )

    print()


# ============================================================
# MULTI-RETAILER SEARCH V2
# ============================================================


def extract_price_from_text(text):
    """Extract a visible AUD price from retailer search-result text."""
    matches = re.findall(r"\$\s*([0-9][0-9,]*(?:\.\d{1,2})?)", str(text or ""))
    if not matches:
        return None
    try:
        return float(matches[-1].replace(",", ""))
    except ValueError:
        return None

def _snapshot_search_links(driver, selectors):
    """
    Take a stable snapshot of candidate product links from a retailer
    search page. We return plain strings instead of live Selenium
    elements so dynamic page refreshes cannot make them stale.
    """

    selector_list = ", ".join(selectors)

    raw_links = driver.execute_script(
        """
        const selector = arguments[0];
        return Array.from(document.querySelectorAll(selector)).map(function(link) {
            const text = (
                link.getAttribute("aria-label")
                || link.getAttribute("title")
                || link.innerText
                || link.textContent
                || ""
            ).trim();

            return {
                url: link.href || "",
                title: text
            };
        });
        """,
        selector_list,
    )

    results = []
    seen_urls = set()

    for item in raw_links:
        url = (item.get("url") or "").strip()
        title = (item.get("title") or "").strip()

        if not url or not title or url in seen_urls:
            continue

        seen_urls.add(url)
        results.append({"name": title, "url": url, "price": extract_price_from_text(title)})

    return results


def search_bunnings(product_name):
    """
    Search Bunnings Australia for candidate products.

    Bunnings product links normally contain a product-code suffix such as
    _p0343916. The selectors below intentionally include a few variants so
    small frontend changes at Bunnings do not immediately break Wishlist.
    """

    search_text = build_search_terms(product_name)
    encoded_search = quote_plus(search_text)

    search_url = (
        "https://www.bunnings.com.au/search/products?q="
        + encoded_search
    )

    print()
    print("=" * 60)
    print("SEARCHING BUNNINGS")
    print("=" * 60)
    print(f"Search Text: {search_text}")
    print(f"Search URL: {search_url}")
    print()

    driver = None

    try:
        driver = create_price_driver()
        driver.get(search_url)

        selectors = [
            "a[href*='_p']",
            "a[href*='/p/']",
            "a[href*='/products/']",
        ]

        WebDriverWait(driver, 12).until(
            lambda current_driver: any(
                current_driver.find_elements(By.CSS_SELECTOR, selector)
                for selector in selectors
            )
        )

        results = _snapshot_search_links(driver, selectors)

        # Remove obvious navigation/category links while preserving real
        # product URLs.
        filtered = []

        for result in results:
            url = result["url"].lower()
            name = result["name"].strip()

            looks_like_product = (
                "_p" in url
                or "/p/" in url
            )

            if not looks_like_product:
                continue

            if len(name) < 5:
                continue

            filtered.append(result)

        return filtered

    except Exception as error:
        print()
        print("BUNNINGS SEARCH FAILED")
        print(f"Reason: {error}")
        return []

    finally:
        if driver is not None:
            driver.quit()


def get_live_retailer_price(store_name, candidate):
    """
    Read the live price of one comparison candidate using Wishlist's
    existing retailer price selector.
    """

    if candidate is None:
        return None

    embedded_price = candidate.get("price")
    if embedded_price is not None:
        return float(embedded_price)

    price_selector = get_price_selector(store_name)

    if not price_selector:
        raise ValueError(
            f"No price selector is configured for {store_name}."
        )

    temporary_product = {
        "url": candidate["url"],
        "price_selector": price_selector,
    }

    return get_product_price(temporary_product)


def price_top_candidates(store_name, scored_results, limit=5):
    """
    Attach live prices to the strongest few candidates.

    The matcher is still being refined, so Wishlist deliberately exposes
    several candidates instead of pretending the first result is always
    correct. To keep comparisons reasonably fast, only the first `limit`
    candidates are live-price checked.
    """

    priced_results = []

    for result in scored_results[:limit]:
        priced = dict(result)
        priced["price"] = None
        priced["price_error"] = None

        try:
            priced["price"] = get_live_retailer_price(
                store_name,
                result,
            )
        except Exception as error:
            priced["price_error"] = str(error)

        priced_results.append(priced)

    return priced_results


def build_retailer_comparison(
    store_name,
    tracked_product_name,
    search_function,
    *,
    price_limit=5,
):
    """
    Search, score and price one retailer.

    Returns a consistent response shape that can be rendered by the web
    comparison page regardless of retailer.
    """

    raw_results = search_function(tracked_product_name)

    scored_results = score_search_results(
        tracked_product_name,
        raw_results,
    )

    priced_top = price_top_candidates(
        store_name,
        scored_results,
        limit=price_limit,
    )

    strongest = priced_top[0] if priced_top else None

    return {
        "store": store_name,
        "searched_count": len(scored_results),
        "strongest_match": strongest,
        "matches": priced_top,
    }
