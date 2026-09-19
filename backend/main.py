# ============================================================
# WISHLIST BACKEND
# ============================================================

import json
import os

from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from comparison_v2.api_routes import router as comparison_v2_router
from comparison_routes import router as comparison_router

from email_sender import (
    send_digest_email,
    send_product_alert,
)

from price_checker import (
    create_price_driver,
    get_product_image_url,
    get_product_price,
    get_product_title,
)

from product_store import (
    get_product_by_id,
    load_products,
    save_products,
)

from store_manager import (
    get_price_selector,
    get_store_name_from_url,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

ALERT_EMAIL = os.getenv(
    "TEST_ALERT_EMAIL"
)


# ============================================================
# SETTINGS FILE
# ============================================================

SETTINGS_FILE = (
    Path(__file__).resolve().parent
    / "settings.json"
)


DEFAULT_SETTINGS = {
    "digestPreferences": {
        "contentMode": "ALL_PRODUCTS",
    },
    "lastDailyDigestSentAt": None,
    "lastWeeklyDigestSentAt": None,
}


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Wishlist API",
    version="0.6.0",
)

app.include_router(comparison_router)
app.include_router(comparison_v2_router)

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# CONSTANTS
# ============================================================

ALERT_MODES = {
    "TARGET_REACHED",
    "PRICE_DROP",
    "PRICE_CHANGE",
    "DAILY_DIGEST",
    "WEEKLY_DIGEST",
    "OFF",
}


DIGEST_CONTENT_MODES = {
    "ALL_PRODUCTS",
    "CHANGED_ONLY",
}


# ============================================================
# REQUEST MODELS
# ============================================================

class PriceCheckRequest(BaseModel):
    url: str


class AnalyseProductRequest(BaseModel):
    url: str


class AddProductRequest(BaseModel):
    url: str
    displayName: str
    store: str
    category: str
    currentPrice: float
    imageUrl: str | None = None
    targetPrice: float | None = None
    notes: str | None = None


class UpdateTargetPriceRequest(BaseModel):
    targetPrice: float | None = None


class UpdateAlertSettingsRequest(BaseModel):
    mode: str
    emailEnabled: bool = True


class UpdateDigestPreferencesRequest(BaseModel):
    contentMode: str


class QueueDigestTestEventRequest(BaseModel):
    cadence: str
    previousPrice: float | None = None


# ============================================================
# SETTINGS HELPERS
# ============================================================

def load_settings():
    if not SETTINGS_FILE.exists():

        save_settings(
            DEFAULT_SETTINGS.copy()
        )

        return DEFAULT_SETTINGS.copy()

    try:

        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:

            data = json.load(
                file
            )

    except Exception:

        data = {}

    settings = {
        **DEFAULT_SETTINGS,
        **data,
    }

    digest_preferences = {
        **DEFAULT_SETTINGS[
            "digestPreferences"
        ],

        **settings.get(
            "digestPreferences",
            {},
        ),
    }

    content_mode = (
        digest_preferences.get(
            "contentMode",
            "ALL_PRODUCTS",
        )
    )

    if (
        content_mode
        not in DIGEST_CONTENT_MODES
    ):
        content_mode = (
            "ALL_PRODUCTS"
        )

    settings[
        "digestPreferences"
    ] = {
        "contentMode": content_mode,
    }

    return settings


def save_settings(
    settings: dict,
):
    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            settings,
            file,
            indent=2,
        )


# ============================================================
# ALERT SETTINGS HELPERS
# ============================================================

def get_alert_mode(
    product: dict,
):
    settings = product.get(
        "alertSettings"
    )

    if not isinstance(
        settings,
        dict,
    ):
        return "TARGET_REACHED"

    mode = settings.get(
        "mode",
        "TARGET_REACHED",
    )

    if mode not in ALERT_MODES:
        return "TARGET_REACHED"

    return mode


def email_alerts_enabled(
    product: dict,
):
    settings = product.get(
        "alertSettings"
    )

    if not isinstance(
        settings,
        dict,
    ):
        return True

    return bool(
        settings.get(
            "emailEnabled",
            True,
        )
    )


def ensure_alert_settings(
    product: dict,
):
    settings = product.get(
        "alertSettings"
    )

    if not isinstance(
        settings,
        dict,
    ):
        settings = {}

    mode = settings.get(
        "mode",
        "TARGET_REACHED",
    )

    if mode not in ALERT_MODES:
        mode = "TARGET_REACHED"

    product[
        "alertSettings"
    ] = {
        "mode": mode,

        "emailEnabled": bool(
            settings.get(
                "emailEnabled",
                True,
            )
        ),
    }

    if not isinstance(
        product.get(
            "digestEvents"
        ),
        list,
    ):
        product[
            "digestEvents"
        ] = []

    return product


# ============================================================
# TARGET STATE
# ============================================================

def update_target_state(
    product: dict,
    *,
    allow_new_notification: bool = True,
):
    current_price = product.get(
        "currentPrice"
    )

    target_price = product.get(
        "targetPrice"
    )

    previous_reached = bool(
        product.get(
            "targetReached",
            False,
        )
    )

    if (
        current_price is None
        or target_price is None
    ):

        product[
            "targetReached"
        ] = False

        product[
            "targetDifference"
        ] = None

        product[
            "targetStatus"
        ] = (
            "NO_TARGET"
            if target_price is None
            else "NO_CURRENT_PRICE"
        )

        if target_price is None:
            product[
                "notificationPending"
            ] = False

        return product

    target_difference = round(
        float(current_price)
        - float(target_price),
        2,
    )

    target_reached = (
        float(current_price)
        <= float(target_price)
    )

    product[
        "targetReached"
    ] = target_reached

    product[
        "targetDifference"
    ] = target_difference

    product[
        "targetStatus"
    ] = (
        "TARGET_REACHED"
        if target_reached
        else "ABOVE_TARGET"
    )

    if (
        allow_new_notification
        and target_reached
        and not previous_reached
    ):

        triggered_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        product[
            "notificationPending"
        ] = True

        product[
            "notificationTriggeredAt"
        ] = triggered_at

        product[
            "notificationReason"
        ] = "TARGET_REACHED"

    if (
        not target_reached
        and product.get(
            "notificationPending"
        )
        and product.get(
            "notificationReason"
        )
        == "TARGET_REACHED"
    ):

        product[
            "notificationPending"
        ] = False

    return product


# ============================================================
# EMAIL DELIVERY
# ============================================================

def try_send_pending_product_alert(
    product: dict,
):
    if not product.get(
        "notificationPending"
    ):

        return {
            "attempted": False,
            "sent": False,
            "reason": "NO_PENDING_ALERT",
        }

    if not email_alerts_enabled(
        product
    ):

        return {
            "attempted": False,
            "sent": False,
            "reason": "EMAIL_DISABLED",
        }

    if not ALERT_EMAIL:

        product[
            "notificationLastError"
        ] = (
            "TEST_ALERT_EMAIL "
            "is not configured."
        )

        return {
            "attempted": True,
            "sent": False,
            "reason": "NO_ALERT_EMAIL",
        }

    try:

        result = (
            send_product_alert(
                to_email=ALERT_EMAIL,
                product=product,
            )
        )

        sent_at = (
            datetime.now(
                timezone.utc
            ).isoformat()
        )

        product[
            "notificationPending"
        ] = False

        product[
            "notificationSentAt"
        ] = sent_at

        product[
            "notificationLastError"
        ] = None

        return {
            "attempted": True,
            "sent": True,
            "sentAt": sent_at,
            "result": str(result),
        }

    except Exception as error:

        product[
            "notificationLastError"
        ] = str(error)

        return {
            "attempted": True,
            "sent": False,
            "error": str(error),
        }


# ============================================================
# NEW PRODUCT DEFAULTS
# ============================================================

def prepare_new_product_target_state(
    product: dict,
):
    product.setdefault(
        "targetReached",
        False,
    )

    product.setdefault(
        "targetDifference",
        None,
    )

    product.setdefault(
        "targetStatus",
        "NO_TARGET",
    )

    product.setdefault(
        "notificationPending",
        False,
    )

    product.setdefault(
        "notificationTriggeredAt",
        None,
    )

    product.setdefault(
        "notificationReason",
        None,
    )

    product.setdefault(
        "notificationSentAt",
        None,
    )

    product.setdefault(
        "notificationLastError",
        None,
    )

    product.setdefault(
        "digestEvents",
        [],
    )

    product = (
        ensure_alert_settings(
            product
        )
    )

    return update_target_state(
        product,
        allow_new_notification=False,
    )


# ============================================================
# DIGEST HELPERS
# ============================================================

def get_digest_events_for_cadence(
    product: dict,
    cadence: str,
):
    events = product.get(
        "digestEvents"
    )

    if not isinstance(
        events,
        list,
    ):
        return []

    return [
        event
        for event in events
        if event.get(
            "cadence"
        ) == cadence
    ]


def prepare_digest_products(
    products: list,
    cadence: str,
    content_mode: str,
):
    prepared = []

    for product in products:

        product_copy = dict(
            product
        )

        matching_events = (
            get_digest_events_for_cadence(
                product,
                cadence,
            )
        )

        changed = (
            len(
                matching_events
            )
            > 0
        )

        if (
            content_mode
            == "CHANGED_ONLY"
            and not changed
        ):
            continue

        product_copy[
            "_digestChanged"
        ] = changed

        if matching_events:

            product_copy[
                "_digestLatestChange"
            ] = matching_events[-1]

        else:

            product_copy[
                "_digestLatestChange"
            ] = None

        prepared.append(
            product_copy
        )

    return prepared


def clear_digest_events(
    products: list,
    cadence: str,
):
    for product in products:

        events = product.get(
            "digestEvents"
        )

        if not isinstance(
            events,
            list,
        ):
            continue

        product[
            "digestEvents"
        ] = [
            event
            for event in events
            if event.get(
                "cadence"
            ) != cadence
        ]


def process_digest(
    cadence: str,
):
    if cadence not in {
        "DAILY_DIGEST",
        "WEEKLY_DIGEST",
    }:

        raise ValueError(
            "Unsupported digest cadence."
        )

    if not ALERT_EMAIL:

        return {
            "success": False,
            "sent": False,
            "reason": (
                "TEST_ALERT_EMAIL "
                "is not configured."
            ),
        }

    products = load_products()

    for product in products:
        ensure_alert_settings(
            product
        )

    # At least one product needs this digest mode enabled.
    subscribed_products = [
        product
        for product in products
        if (
            get_alert_mode(
                product
            )
            == cadence
            and email_alerts_enabled(
                product
            )
        )
    ]

    if not subscribed_products:

        return {
            "success": True,
            "sent": False,
            "reason": (
                "NO_PRODUCTS_USING_THIS_DIGEST"
            ),
        }

    settings = load_settings()

    content_mode = (
        settings[
            "digestPreferences"
        ][
            "contentMode"
        ]
    )

    email_products = (
        prepare_digest_products(
            products,
            cadence,
            content_mode,
        )
    )

    if (
        content_mode
        == "CHANGED_ONLY"
        and not email_products
    ):

        return {
            "success": True,
            "sent": False,
            "reason": "NO_PRICE_CHANGES",
        }

    try:

        result = send_digest_email(
            to_email=ALERT_EMAIL,
            cadence=cadence,
            products=email_products,
            content_mode=content_mode,
        )

    except Exception as error:

        return {
            "success": False,
            "sent": False,
            "error": str(error),
        }

    # Important:
    # only clear digest events AFTER successful delivery.
    clear_digest_events(
        products,
        cadence,
    )

    save_products(
        products
    )

    sent_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    if cadence == "DAILY_DIGEST":

        settings[
            "lastDailyDigestSentAt"
        ] = sent_at

    else:

        settings[
            "lastWeeklyDigestSentAt"
        ] = sent_at

    save_settings(
        settings
    )

    return {
        "success": True,
        "sent": True,
        "sentAt": sent_at,
        "cadence": cadence,
        "contentMode": content_mode,
        "productCount": len(
            email_products
        ),
        "result": str(result),
    }


# ============================================================
# STATUS
# ============================================================

@app.get("/")
def backend_status():

    return {
        "success": True,
        "message": (
            "Wishlist backend is running"
        ),
    }


# ============================================================
# GET PRODUCTS
# ============================================================

@app.get("/products")
def get_products():

    products = load_products()

    updated = False

    for product in products:

        before = product.get(
            "alertSettings"
        )

        ensure_alert_settings(
            product
        )

        if (
            before
            != product.get(
                "alertSettings"
            )
        ):
            updated = True

    if updated:
        save_products(
            products
        )

    return products


# ============================================================
# REMOVE PRODUCT
# ============================================================

@app.delete(
    "/products/{product_id}"
)
def remove_product(
    product_id: str,
):

    products = load_products()

    updated_products = [
        product
        for product in products
        if product.get(
            "id"
        )
        != product_id
    ]

    if (
        len(
            updated_products
        )
        == len(
            products
        )
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    save_products(
        updated_products
    )

    return {
        "success": True,
        "removedProductId": (
            product_id
        ),
    }


# ============================================================
# SIMPLE PRICE CHECK
# ============================================================

@app.post("/check-price")
def check_price(
    request: PriceCheckRequest,
):

    store_name = (
        get_store_name_from_url(
            request.url
        )
    )

    if (
        store_name
        == "Unknown Store"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Wishlist does not support "
                "this retailer yet."
            ),
        )

    price_selector = (
        get_price_selector(
            store_name
        )
    )

    if not price_selector:

        raise HTTPException(
            status_code=400,
            detail=(
                f"No price selector is "
                f"configured for "
                f"{store_name}."
            ),
        )

    try:

        current_price = (
            get_product_price(
                {
                    "url": (
                        request.url
                    ),
                    "price_selector": (
                        price_selector
                    ),
                }
            )
        )

        return {
            "success": True,
            "store": store_name,
            "price": current_price,
            "url": request.url,
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Price check failed: "
                f"{error}"
            ),
        ) from error


# ============================================================
# ANALYSE PRODUCT
# ============================================================

@app.post("/analyse-product")
def analyse_product(
    request: AnalyseProductRequest,
):

    store_name = (
        get_store_name_from_url(
            request.url
        )
    )

    if (
        store_name
        == "Unknown Store"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Wishlist does not support "
                "this retailer yet."
            ),
        )

    price_selector = (
        get_price_selector(
            store_name
        )
    )

    if not price_selector:

        raise HTTPException(
            status_code=400,
            detail=(
                f"No price selector is "
                f"configured for "
                f"{store_name}."
            ),
        )

    product = {
        "url": (
            request.url
        ),
        "price_selector": (
            price_selector
        ),
    }

    driver = None

    try:

        driver = (
            create_price_driver()
        )

        current_price = (
            get_product_price(
                product,
                driver=driver,
            )
        )

        product_title = (
            get_product_title(
                product,
                driver=driver,
            )
        )

        image_url = (
            get_product_image_url(
                product,
                driver=driver,
                navigate=False,
            )
        )

        return {
            "success": True,
            "url": request.url,
            "store": store_name,
            "title": product_title,
            "currentPrice": (
                current_price
            ),
            "imageUrl": (
                image_url
            ),
        }

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                "Product analysis failed: "
                f"{error}"
            ),
        ) from error

    finally:

        if driver is not None:
            driver.quit()


# ============================================================
# ADD PRODUCT
# ============================================================

@app.post("/products")
def add_product(
    request: AddProductRequest,
):

    products = load_products()

    if any(
        product.get(
            "url"
        )
        == request.url
        for product in products
    ):

        raise HTTPException(
            status_code=409,
            detail=(
                "This product is already "
                "in your Wishlist."
            ),
        )

    store_name = (
        get_store_name_from_url(
            request.url
        )
    )

    if (
        store_name
        == "Unknown Store"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Wishlist does not support "
                "this retailer yet."
            ),
        )

    price_selector = (
        get_price_selector(
            store_name
        )
    )

    added_order = (
        max(
            [
                int(
                    product.get(
                        "addedOrder",
                        0,
                    )
                )
                for product
                in products
            ],
            default=0,
        )
        + 1
    )

    checked_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    new_product = {
        "id": (
            f"product-"
            f"{uuid4().hex[:10]}"
        ),

        "name": (
            request.displayName
        ),

        "displayName": (
            request.displayName
        ),

        "store": (
            store_name
        ),

        "category": (
            request.category
            or "Other"
        ),

        "url": (
            request.url
        ),

        "targetPrice": (
            request.targetPrice
        ),

        "imageUrl": (
            request.imageUrl
        ),

        "currentPrice": (
            request.currentPrice
        ),

        "addedPrice": (
            request.currentPrice
        ),

        "priceSelector": (
            price_selector
        ),

        "source": "website",

        "addedOrder": (
            added_order
        ),

        "lastChecked": (
            checked_at
        ),

        "notes": (
            request.notes
            or ""
        ),

        "priceHistory": [
            {
                "checkedAt": (
                    checked_at
                ),

                "price": (
                    request.currentPrice
                ),
            }
        ],

        "alertSettings": {
            "mode": (
                "TARGET_REACHED"
            ),

            "emailEnabled": True,
        },

        "digestEvents": [],
    }

    new_product = (
        prepare_new_product_target_state(
            new_product
        )
    )

    products.append(
        new_product
    )

    save_products(
        products
    )

    return {
        "success": True,
        "product": new_product,
    }


# ============================================================
# UPDATE ALERT SETTINGS
# ============================================================

@app.patch(
    "/products/{product_id}"
    "/alert-settings"
)
def update_alert_settings(
    product_id: str,
    request: UpdateAlertSettingsRequest,
):

    products, product_index = (
        get_product_by_id(
            product_id
        )
    )

    if (
        products is None
        or product_index is None
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    mode = (
        request.mode
        .upper()
        .strip()
    )

    if mode not in ALERT_MODES:

        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported alert "
                f"mode: {mode}"
            ),
        )

    product = (
        products[
            product_index
        ]
    )

    product[
        "alertSettings"
    ] = {
        "mode": mode,

        "emailEnabled": (
            request.emailEnabled
        ),
    }

    products[
        product_index
    ] = product

    save_products(
        products
    )

    return {
        "success": True,
        "product": product,
    }


# ============================================================
# DIGEST SETTINGS
# ============================================================

@app.get("/settings/digest")
def get_digest_settings():

    settings = load_settings()

    return {
        "success": True,
        **settings[
            "digestPreferences"
        ],

        "lastDailyDigestSentAt": (
            settings.get(
                "lastDailyDigestSentAt"
            )
        ),

        "lastWeeklyDigestSentAt": (
            settings.get(
                "lastWeeklyDigestSentAt"
            )
        ),
    }


@app.patch("/settings/digest")
def update_digest_settings(
    request: UpdateDigestPreferencesRequest,
):

    content_mode = (
        request.contentMode
        .upper()
        .strip()
    )

    if (
        content_mode
        not in DIGEST_CONTENT_MODES
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "contentMode must be "
                "ALL_PRODUCTS or "
                "CHANGED_ONLY."
            ),
        )

    settings = load_settings()

    settings[
        "digestPreferences"
    ][
        "contentMode"
    ] = content_mode

    save_settings(
        settings
    )

    return {
        "success": True,
        "contentMode": (
            content_mode
        ),
    }


# ============================================================
# GET PENDING IMMEDIATE ALERTS
# ============================================================

@app.get("/alerts/pending")
def get_pending_alerts():

    products = load_products()

    pending_alerts = []

    for product in products:

        if product.get(
            "notificationPending"
        ):

            pending_alerts.append(
                {
                    "productId": (
                        product.get(
                            "id"
                        )
                    ),

                    "name": (
                        product.get(
                            "displayName"
                        )
                        or product.get(
                            "name"
                        )
                    ),

                    "store": (
                        product.get(
                            "store"
                        )
                    ),

                    "url": (
                        product.get(
                            "url"
                        )
                    ),

                    "imageUrl": (
                        product.get(
                            "imageUrl"
                        )
                    ),

                    "currentPrice": (
                        product.get(
                            "currentPrice"
                        )
                    ),

                    "targetPrice": (
                        product.get(
                            "targetPrice"
                        )
                    ),

                    "targetDifference": (
                        product.get(
                            "targetDifference"
                        )
                    ),

                    "triggeredAt": (
                        product.get(
                            "notificationTriggeredAt"
                        )
                    ),

                    "reason": (
                        product.get(
                            "notificationReason"
                        )
                    ),
                }
            )

    return {
        "success": True,

        "count": len(
            pending_alerts
        ),

        "alerts": (
            pending_alerts
        ),
    }


# ============================================================
# SEND PENDING IMMEDIATE ALERTS
# ============================================================

@app.post("/alerts/send-pending")
def send_pending_alerts():

    products = load_products()

    sent_alerts = []

    failed_alerts = []

    for product in products:

        if not product.get(
            "notificationPending"
        ):
            continue

        result = (
            try_send_pending_product_alert(
                product
            )
        )

        if result.get(
            "sent"
        ):

            sent_alerts.append(
                {
                    "productId": (
                        product.get(
                            "id"
                        )
                    ),

                    "name": (
                        product.get(
                            "displayName"
                        )
                        or product.get(
                            "name"
                        )
                    ),

                    "result": (
                        result
                    ),
                }
            )

        else:

            failed_alerts.append(
                {
                    "productId": (
                        product.get(
                            "id"
                        )
                    ),

                    "name": (
                        product.get(
                            "displayName"
                        )
                        or product.get(
                            "name"
                        )
                    ),

                    "result": (
                        result
                    ),
                }
            )

    save_products(
        products
    )

    return {
        "success": (
            len(
                failed_alerts
            )
            == 0
        ),

        "sentCount": len(
            sent_alerts
        ),

        "failedCount": len(
            failed_alerts
        ),

        "sent": sent_alerts,

        "failed": failed_alerts,
    }


# ============================================================
# SEND DAILY DIGEST
# ============================================================

@app.post(
    "/alerts/send-daily-digest"
)
def send_daily_digest():

    return process_digest(
        "DAILY_DIGEST"
    )


# ============================================================
# SEND WEEKLY DIGEST
# ============================================================

@app.post(
    "/alerts/send-weekly-digest"
)
def send_weekly_digest():

    return process_digest(
        "WEEKLY_DIGEST"
    )


# ============================================================
# TEST DIGEST EVENT
#
# Development helper.
# Lets us test a digest without waiting for a real shop price
# to change.
# ============================================================

@app.post(
    "/alerts/{product_id}"
    "/queue-test-digest-event"
)
def queue_test_digest_event(
    product_id: str,
    request: QueueDigestTestEventRequest,
):

    cadence = (
        request.cadence
        .upper()
        .strip()
    )

    if cadence not in {
        "DAILY_DIGEST",
        "WEEKLY_DIGEST",
    }:

        raise HTTPException(
            status_code=400,
            detail=(
                "cadence must be "
                "DAILY_DIGEST or "
                "WEEKLY_DIGEST."
            ),
        )

    products, product_index = (
        get_product_by_id(
            product_id
        )
    )

    if (
        products is None
        or product_index is None
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    product = (
        products[
            product_index
        ]
    )

    ensure_alert_settings(
        product
    )

    current_price = (
        product.get(
            "currentPrice"
        )
    )

    if current_price is None:

        raise HTTPException(
            status_code=400,
            detail=(
                "Product has no "
                "current price."
            ),
        )

    previous_price = (
        request.previousPrice
    )

    if previous_price is None:

        previous_price = (
            float(
                current_price
            )
            + 10
        )

    checked_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    product[
        "digestEvents"
    ].append(
        {
            "checkedAt": (
                checked_at
            ),

            "previousPrice": (
                previous_price
            ),

            "currentPrice": (
                current_price
            ),

            "cadence": (
                cadence
            ),

            "testEvent": True,
        }
    )

    products[
        product_index
    ] = product

    save_products(
        products
    )

    return {
        "success": True,
        "product": product,
    }


# ============================================================
# ACKNOWLEDGE IMMEDIATE ALERT
# ============================================================

@app.post(
    "/alerts/{product_id}"
    "/acknowledge"
)
def acknowledge_alert(
    product_id: str,
):

    products, product_index = (
        get_product_by_id(
            product_id
        )
    )

    if (
        products is None
        or product_index is None
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    product = (
        products[
            product_index
        ]
    )

    product[
        "notificationPending"
    ] = False

    product[
        "lastNotificationAcknowledgedAt"
    ] = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    products[
        product_index
    ] = product

    save_products(
        products
    )

    return {
        "success": True,
        "product": product,
    }


# ============================================================
# RECALCULATE ALERTS
# ============================================================

@app.post(
    "/alerts/recalculate"
)
def recalculate_all_alerts():

    products = load_products()

    updated_products = []

    for product in products:

        product = (
            ensure_alert_settings(
                product
            )
        )

        product.setdefault(
            "targetReached",
            False,
        )

        product.setdefault(
            "notificationPending",
            False,
        )

        product.setdefault(
            "digestEvents",
            [],
        )

        updated_products.append(
            update_target_state(
                product,
                allow_new_notification=False,
            )
        )

    save_products(
        updated_products
    )

    return {
        "success": True,

        "count": len(
            updated_products
        ),

        "products": (
            updated_products
        ),
    }


# ============================================================
# UPDATE TARGET PRICE
# ============================================================

@app.patch(
    "/products/{product_id}"
    "/target-price"
)
def update_target_price(
    product_id: str,
    request: UpdateTargetPriceRequest,
):

    products, product_index = (
        get_product_by_id(
            product_id
        )
    )

    if (
        products is None
        or product_index is None
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    if (
        request.targetPrice
        is not None
        and request.targetPrice < 0
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Target price cannot "
                "be negative."
            ),
        )

    product = (
        products[
            product_index
        ]
    )

    product = (
        ensure_alert_settings(
            product
        )
    )

    product[
        "targetPrice"
    ] = request.targetPrice

    product = (
        update_target_state(
            product,
            allow_new_notification=True,
        )
    )

    alert_mode = (
        get_alert_mode(
            product
        )
    )

    if (
        product.get(
            "notificationPending"
        )
        and alert_mode != "OFF"
        and email_alerts_enabled(
            product
        )
    ):

        email_result = (
            try_send_pending_product_alert(
                product
            )
        )

    else:

        email_result = {
            "attempted": False,
            "sent": False,
            "reason": (
                "NO_ALERT_REQUIRED"
            ),
        }

    products[
        product_index
    ] = product

    save_products(
        products
    )

    return {
        "success": True,

        "product": product,

        "emailAlert": (
            email_result
        ),
    }


# ============================================================
# CHECK + SAVE PRODUCT PRICE
# ============================================================

@app.post(
    "/products/{product_id}"
    "/check-price"
)
def check_and_save_product_price(
    product_id: str,
):

    products, product_index = (
        get_product_by_id(
            product_id
        )
    )

    if (
        products is None
        or product_index is None
    ):

        raise HTTPException(
            status_code=404,
            detail=(
                "Wishlist product "
                "was not found."
            ),
        )

    product = (
        products[
            product_index
        ]
    )

    product = (
        ensure_alert_settings(
            product
        )
    )

    store_name = (
        get_store_name_from_url(
            product[
                "url"
            ]
        )
    )

    if (
        store_name
        == "Unknown Store"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Wishlist does not "
                "support this "
                "retailer yet."
            ),
        )

    price_selector = (
        product.get(
            "priceSelector"
        )
        or get_price_selector(
            store_name
        )
    )

    if not price_selector:

        raise HTTPException(
            status_code=400,
            detail=(
                f"No price selector "
                f"is configured for "
                f"{store_name}."
            ),
        )

    try:

        current_price = (
            get_product_price(
                {
                    "url": (
                        product[
                            "url"
                        ]
                    ),

                    "price_selector": (
                        price_selector
                    ),
                }
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Price check failed: "
                f"{error}"
            ),
        ) from error

    checked_at = (
        datetime.now(
            timezone.utc
        ).isoformat()
    )

    previous_price = (
        product.get(
            "currentPrice"
        )
    )

    if (
        product.get(
            "addedPrice"
        )
        is None
    ):

        product[
            "addedPrice"
        ] = current_price

    product[
        "previousPrice"
    ] = previous_price

    product[
        "currentPrice"
    ] = current_price

    product[
        "lastChecked"
    ] = checked_at

    price_history = (
        product.get(
            "priceHistory"
        )
    )

    if not isinstance(
        price_history,
        list,
    ):

        price_history = []

    price_history.append(
        {
            "checkedAt": (
                checked_at
            ),

            "price": (
                current_price
            ),
        }
    )

    product[
        "priceHistory"
    ] = price_history

    price_changed = (
        previous_price is not None

        and float(
            current_price
        )

        != float(
            previous_price
        )
    )

    price_dropped = (
        previous_price is not None

        and float(
            current_price
        )

        < float(
            previous_price
        )
    )

    product = (
        update_target_state(
            product,
            allow_new_notification=True,
        )
    )

    alert_mode = (
        get_alert_mode(
            product
        )
    )

    email_enabled = (
        email_alerts_enabled(
            product
        )
    )

    target_alert_created = (
        product.get(
            "notificationPending"
        )

        and product.get(
            "notificationReason"
        )

        == "TARGET_REACHED"
    )

    # --------------------------------------------------------
    # TARGET REACHED
    #
    # Immediate priority even for daily/weekly users.
    # --------------------------------------------------------

    if (
        target_alert_created
        and email_enabled
        and alert_mode != "OFF"
    ):

        email_result = (
            try_send_pending_product_alert(
                product
            )
        )

    # --------------------------------------------------------
    # EVERY PRICE DROP
    # --------------------------------------------------------

    elif (
        alert_mode
        == "PRICE_DROP"

        and email_enabled

        and price_dropped
    ):

        product[
            "notificationPending"
        ] = True

        product[
            "notificationReason"
        ] = "PRICE_DROP"

        product[
            "notificationTriggeredAt"
        ] = checked_at

        email_result = (
            try_send_pending_product_alert(
                product
            )
        )

    # --------------------------------------------------------
    # EVERY PRICE CHANGE
    # --------------------------------------------------------

    elif (
        alert_mode
        == "PRICE_CHANGE"

        and email_enabled

        and price_changed
    ):

        product[
            "notificationPending"
        ] = True

        product[
            "notificationReason"
        ] = "PRICE_CHANGE"

        product[
            "notificationTriggeredAt"
        ] = checked_at

        email_result = (
            try_send_pending_product_alert(
                product
            )
        )

    # --------------------------------------------------------
    # DAILY / WEEKLY DIGEST
    # --------------------------------------------------------

    elif (
        alert_mode
        in {
            "DAILY_DIGEST",
            "WEEKLY_DIGEST",
        }

        and price_changed
    ):

        digest_events = (
            product.get(
                "digestEvents"
            )
        )

        if not isinstance(
            digest_events,
            list,
        ):

            digest_events = []

        digest_events.append(
            {
                "checkedAt": (
                    checked_at
                ),

                "previousPrice": (
                    previous_price
                ),

                "currentPrice": (
                    current_price
                ),

                "cadence": (
                    alert_mode
                ),

                "testEvent": False,
            }
        )

        product[
            "digestEvents"
        ] = digest_events

        email_result = {
            "attempted": False,
            "sent": False,
            "reason": (
                "QUEUED_FOR_DIGEST"
            ),
        }

    else:

        email_result = {
            "attempted": False,
            "sent": False,
            "reason": (
                "NO_ALERT_REQUIRED"
            ),
        }

    products[
        product_index
    ] = product

    save_products(
        products
    )

    return {
        "success": True,

        "product": product,

        "emailAlert": (
            email_result
        ),
    }
