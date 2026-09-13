# ============================================================
# WISHLIST - PRODUCT STORAGE
# ============================================================
#
# Temporary local persistence for the website build.
# This will later be replaced by the real database.
# ============================================================

import json
import os
from pathlib import Path


BACKEND_FOLDER = Path(__file__).resolve().parent
PRODUCTS_FILE = BACKEND_FOLDER / "products.json"


def load_products():
    """Load the complete Wishlist product list from products.json."""
    if not PRODUCTS_FILE.exists():
        save_products([])
        return []

    try:
        with PRODUCTS_FILE.open("r", encoding="utf-8") as file:
            products = json.load(file)

        if not isinstance(products, list):
            raise ValueError("products.json does not contain a product list.")

        return products

    except (json.JSONDecodeError, ValueError):
        raise RuntimeError(
            "Wishlist could not read backend/products.json."
        )


def save_products(products):
    """
    Save products safely.

    Write to a temporary file first, then replace products.json only
    after the new file has been written successfully.
    """
    temporary_file = PRODUCTS_FILE.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            products,
            file,
            indent=2,
            ensure_ascii=False,
        )

    os.replace(temporary_file, PRODUCTS_FILE)


def get_product_by_id(product_id):
    """Return one product and its index, or (None, None) when missing."""
    products = load_products()

    for index, product in enumerate(products):
        if product.get("id") == product_id:
            return products, index

    return None, None
