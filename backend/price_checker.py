# ============================================================
# WISHLIST - PRICE CHECKER
# ============================================================
#
# Website/backend version of the working desktop Wishlist checker.
# Includes:
# - live price checking
# - retailer product title lookup
# - retailer product image lookup
#
# This fixes the backend import error by restoring the helper
# functions required by main.py.
# ============================================================

import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from store_manager import (
    get_store_name_from_url,
    get_image_selector,
)


# ============================================================
# CLEAN PRICE
# ============================================================

def clean_price(price_text):
    """
    Convert retailer price text such as '$399.00' into 399.0.
    """
    if price_text is None:
        raise ValueError("Retailer returned an empty price.")

    cleaned = (
        str(price_text)
        .replace("$", "")
        .replace(",", "")
        .replace("^", "")
        .replace("*", "")
        .replace("#", "")
        .replace("£", "")
        .strip()
    )

    try:
        return float(cleaned)

    except ValueError:
        # Fallback for retailer text that contains extra words.
        match = re.search(r"\d+(?:\.\d{1,2})?", cleaned)

        if not match:
            raise ValueError(
                f"Could not convert retailer price text: {price_text!r}"
            )

        return float(match.group(0))


# ============================================================
# CREATE PRICE-CHECKING BROWSER
# ============================================================

def create_price_driver():
    """
    Create the invisible Chrome browser used for Wishlist checks.
    """
    options = Options()

    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-default-apps")
    options.add_argument("--disable-extensions")

    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(20)

    return driver


# ============================================================
# GET RETAILER PRODUCT TITLE
# ============================================================

def get_product_title(product, driver=None, navigate=True):
    """
    Read the real retailer product title.

    Lookup order:
    1. Main <h1>
    2. Open Graph title metadata
    """
    own_driver = driver is None

    try:
        if own_driver:
            driver = create_price_driver()

        if navigate:
            driver.get(product["url"])

        try:
            title_element = WebDriverWait(
                driver,
                10
            ).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "h1",
                    )
                )
            )

            product_title = title_element.text.strip()

            if product_title:
                return product_title

        except Exception:
            pass

        meta_title = driver.find_elements(
            By.CSS_SELECTOR,
            "meta[property='og:title']",
        )

        if meta_title:
            product_title = (
                meta_title[0]
                .get_attribute("content")
                or ""
            ).strip()

            if product_title:
                return product_title

        raise ValueError(
            "Could not find a retailer product title on the page."
        )

    finally:
        if own_driver and driver is not None:
            driver.quit()


# ============================================================
# GET RETAILER PRODUCT IMAGE URL
# ============================================================

def get_product_image_url(product, driver=None, navigate=True):
    """
    Read the retailer's main product image URL.

    Lookup order:
    1. Open Graph image metadata
    2. Store-specific fallback selector
    3. None
    """
    own_driver = driver is None

    try:
        if own_driver:
            driver = create_price_driver()

        if navigate:
            driver.get(product["url"])

        image_elements = driver.find_elements(
            By.CSS_SELECTOR,
            "meta[property='og:image']",
        )

        for image_element in image_elements:
            image_url = (
                image_element.get_attribute("content")
                or ""
            ).strip()

            if image_url:
                return image_url

        store_name = get_store_name_from_url(
            product["url"]
        )

        image_selector = get_image_selector(
            store_name
        )

        if image_selector:
            try:
                fallback_images = WebDriverWait(
                    driver,
                    8
                ).until(
                    EC.presence_of_all_elements_located(
                        (
                            By.CSS_SELECTOR,
                            image_selector,
                        )
                    )
                )

                for image_element in fallback_images:
                    image_url = (
                        image_element.get_attribute("currentSrc")
                        or image_element.get_attribute("src")
                        or ""
                    ).strip()

                    if image_url:
                        return image_url

            except Exception:
                pass

        return None

    except Exception:
        # Product images are optional and should never prevent
        # a product from being tracked.
        return None

    finally:
        if own_driver and driver is not None:
            driver.quit()


# ============================================================
# GET LIVE PRODUCT PRICE
# ============================================================

def get_product_price(product, driver=None):
    """
    Load one product page and return its live price.

    product must contain:
        url
        price_selector
    """
    own_driver = driver is None

    try:
        if own_driver:
            driver = create_price_driver()

        driver.get(product["url"])

        price_element = WebDriverWait(
            driver,
            10
        ).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    product["price_selector"],
                )
            )
        )

        price_text = (
            price_element.get_attribute("content")
            or price_element.text
        )

        return clean_price(price_text)

    finally:
        if own_driver and driver is not None:
            driver.quit()
