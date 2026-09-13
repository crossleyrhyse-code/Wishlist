# ============================================================
# WISHLIST - SUPPORTED STORES
# ============================================================
#
# Website/backend version of the old Wishlist store manager.
# Store-specific selectors stay in one place so price_checker.py
# does not need retailer-specific code.
# ============================================================

STORES = {
    "4WD Supacentre": {
        "domain": "4wdsupacentre.com.au",
        "price_selector": "[itemprop='price']",
        "image_selector": "img[data-type='image']",
    },
    "Supercheap Auto": {
        "domain": "supercheapauto.com.au",
        "price_selector": ".promo-price",
    },
    "BCF": {
        "domain": "bcf.com.au",
        "price_selector": ".price-sales",
    },
    "Bunnings": {
        "domain": "bunnings.com.au",
        "price_selector": "[data-locator='product-price']",
    },
    "KickAss Products": {
        "domain": "kickassproducts.com.au",
        "price_selector": ".ka-price-dollars",
    },
    "Anaconda": {
        "domain": "anacondastores.com",
        "price_selector": ".amount",
    },
}


def get_store_names():
    """Return every retailer currently supported by Wishlist."""
    return list(STORES.keys())


def get_price_selector(store_name):
    """Return the saved price selector for a retailer."""
    store = STORES.get(store_name)

    if store is None:
        return ""

    return store.get("price_selector", "")


def get_image_selector(store_name):
    """Return a store-specific image selector when one exists."""
    store = STORES.get(store_name)

    if store is None:
        return ""

    return store.get("image_selector", "")


def get_store_domain(store_name):
    """Return a retailer's domain."""
    store = STORES.get(store_name)

    if store is None:
        return ""

    return store.get("domain", "")


def get_store_name_from_url(url):
    """Identify a supported retailer from a product URL."""
    clean_url = url.lower()

    for store_name, store_data in STORES.items():
        domain = store_data.get("domain", "").lower()

        if domain and domain in clean_url:
            return store_name

    return "Unknown Store"
