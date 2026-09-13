# ============================================================
# IMPORTS
# ============================================================

# Regular expressions.
# Used for cleaning product names and finding model information.
import re

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

def classify_product_match(
    name_a,
    name_b,
    exact_threshold=0.80,
    similar_threshold=0.50,
    possible_threshold=0.35,
    identity_threshold=0.75
):
    """
    Classify two retailer product names as:

        EXACT MATCH
        SIMILAR PRODUCT
        POSSIBLE MATCH
        NO MATCH
    """

    name_score = calculate_name_similarity(
        name_a,
        name_b
    )

    identity_score = calculate_identity_similarity(
        name_a,
        name_b
    )

    number_match = important_numbers_match(
        name_a,
        name_b
    )

    brand_match = brands_match(
        name_a,
        name_b
    )

    normal_exact_match = (
        name_score >= exact_threshold
        and number_match
        and brand_match
    )

    identity_exact_match = (
        identity_score >= identity_threshold
        and number_match
        and brand_match
    )

    if (
        normal_exact_match
        or identity_exact_match
    ):
        match_type = "EXACT MATCH"

    elif (
        name_score >= similar_threshold
        or identity_score >= similar_threshold
    ):
        match_type = "SIMILAR PRODUCT"

    elif (
        name_score >= possible_threshold
        or identity_score >= possible_threshold
    ):
        match_type = "POSSIBLE MATCH"

    else:
        match_type = "NO MATCH"

    display_score = max(
        name_score,
        identity_score
    )

    return {
        "score": display_score,
        "percentage": round(
            display_score * 100
        ),
        "name_score": round(
            name_score * 100
        ),
        "identity_score": round(
            identity_score * 100
        ),
        "numbers_match": number_match,
        "brand_match": brand_match,
        "match_type": match_type
    }

def build_search_terms(product_name):
    """
    Create a cleaner search phrase from a retailer product name.
    """

    normalized_name = normalize_product_name(
        product_name
    )

    words = normalized_name.split()

    useful_words = []

    for word in words:

        if word in GENERIC_PRODUCT_WORDS:
            continue

        useful_words.append(
            word
        )

    search_text = " ".join(
        useful_words
    )

    return search_text


# ============================================================
# SEARCH BCF
# ============================================================

def search_bcf(product_name):
    """
    Search BCF for products that might match the tracked product.

    This search version collects product names and URLs.
    """

    search_text = build_search_terms(
        product_name
    )

    encoded_search = quote_plus(
        search_text
    )

    search_url = (
        "https://www.bcf.com.au/search?q="
        + encoded_search
    )

    print()
    print("=" * 60)
    print("SEARCHING BCF")
    print("=" * 60)

    print()
    print(
        f"Search Text: "
        f"{search_text}"
    )

    print(
        f"Search URL: "
        f"{search_url}"
    )

    print()

    driver = None

    try:

        driver = create_price_driver()

        driver.get(
            search_url
        )

        WebDriverWait(
            driver,
            10
        ).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "a[href*='/p/']"
                )
            )
        )

        # ----------------------------------------------------
        # SNAPSHOT THE SEARCH RESULTS
        # ----------------------------------------------------
        #
        # BCF dynamically refreshes parts of its search page.
        # If Selenium keeps individual WebElement references while
        # that happens, Chrome can report:
        #
        #     stale element reference
        #
        # Instead of looping over live WebElements, take one quick
        # JavaScript snapshot of the matching links. The returned
        # values are plain Python strings, so BCF can redraw the page
        # afterwards without invalidating what we already collected.
        raw_product_links = driver.execute_script(
            """
            return Array.from(
                document.querySelectorAll("a[href*='/p/']")
            ).map(function(link) {
                return {
                    url: link.href || "",
                    title: (
                        link.innerText
                        || link.textContent
                        || ""
                    ).trim()
                };
            });
            """
        )

        results = []
        seen_urls = set()

        for link_data in raw_product_links:

            url = (
                link_data.get("url")
                or ""
            ).strip()

            title = (
                link_data.get("title")
                or ""
            ).strip()

            if not url:
                continue

            if url in seen_urls:
                continue

            if not title:
                continue

            seen_urls.add(
                url
            )

            results.append(
                {
                    "name": title,
                    "url": url
                }
            )

        return results

    except Exception as error:

        print()
        print("BCF SEARCH FAILED")

        print(
            f"Reason: "
            f"{error}"
        )

        return []

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
            "match_type": match_result["match_type"]
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
        results.append({"name": title, "url": url})

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
