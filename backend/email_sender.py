# ============================================================
# WISHLIST - EMAIL SENDER
# ============================================================

import os
from html import escape

import resend
from dotenv import load_dotenv


load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY")

ALERT_FROM_EMAIL = os.getenv(
    "ALERT_FROM_EMAIL",
    "Wishlist Price Alerts <alerts@wish-list.com.au>",
)

TEST_ALERT_EMAIL = os.getenv("TEST_ALERT_EMAIL")


# ============================================================
# RESEND CONFIG
# ============================================================

def configure_resend():
    if not RESEND_API_KEY:
        raise RuntimeError(
            "RESEND_API_KEY is missing. Add it to backend/.env"
        )

    resend.api_key = RESEND_API_KEY


# ============================================================
# MONEY
# ============================================================

def money(value):
    if value is None:
        return "—"

    return f"${float(value):,.2f}"


def signed_money(value):
    if value is None:
        return "—"

    value = float(value)

    if value > 0:
        return f"+${value:,.2f}"

    if value < 0:
        return f"-${abs(value):,.2f}"

    return "$0.00"


# ============================================================
# SINGLE PRODUCT ALERT
# ============================================================

def send_price_alert(
    to_email: str,
    product_name: str,
    store: str,
    current_price: float,
    target_price: float | None,
    product_url: str,
    reason: str = "TARGET_REACHED",
    previous_price: float | None = None,
):
    configure_resend()

    safe_name = escape(
        product_name or "Tracked product"
    )

    safe_store = escape(
        store or "Unknown store"
    )

    safe_url = escape(
        product_url or "https://wish-list.com.au"
    )

    current_price = float(
        current_price
    )

    if target_price is not None:
        target_price = float(
            target_price
        )

    if previous_price is not None:
        previous_price = float(
            previous_price
        )

    # --------------------------------------------------------
    # TARGET REACHED
    # --------------------------------------------------------

    if reason == "TARGET_REACHED":

        subject = (
            f"Price alert: {product_name} "
            f"hit your target"
        )

        heading = (
            "Your target price has been reached"
        )

        intro = (
            f"<strong>{safe_name}</strong> "
            f"is now at or below your target price."
        )

        amount_below = None

        if target_price is not None:
            amount_below = max(
                0,
                round(
                    target_price
                    - current_price,
                    2,
                ),
            )

        detail_rows = f"""
            <p>
                <strong>Store:</strong>
                {safe_store}
            </p>

            <p>
                <strong>Current price:</strong>
                {money(current_price)}
            </p>

            <p>
                <strong>Your target:</strong>
                {money(target_price)}
            </p>

            <p>
                <strong>Below target by:</strong>
                {money(amount_below)}
            </p>
        """

    # --------------------------------------------------------
    # PRICE DROP
    # --------------------------------------------------------

    elif reason == "PRICE_DROP":

        subject = (
            f"Price drop: {product_name} "
            f"is cheaper"
        )

        heading = "A tracked price just dropped"

        intro = (
            f"<strong>{safe_name}</strong> "
            f"has dropped in price."
        )

        drop_amount = None

        if previous_price is not None:
            drop_amount = round(
                previous_price
                - current_price,
                2,
            )

        detail_rows = f"""
            <p>
                <strong>Store:</strong>
                {safe_store}
            </p>

            <p>
                <strong>Previous price:</strong>
                {money(previous_price)}
            </p>

            <p>
                <strong>Current price:</strong>
                {money(current_price)}
            </p>

            <p>
                <strong>Price drop:</strong>
                {money(drop_amount)}
            </p>

            <p>
                <strong>Your target:</strong>
                {money(target_price)}
            </p>
        """

    # --------------------------------------------------------
    # PRICE CHANGE
    # --------------------------------------------------------

    else:

        subject = (
            f"Price changed: {product_name}"
        )

        heading = "A tracked price has changed"

        intro = (
            f"<strong>{safe_name}</strong> "
            f"has a new price."
        )

        change_amount = None

        if previous_price is not None:
            change_amount = round(
                current_price
                - previous_price,
                2,
            )

        detail_rows = f"""
            <p>
                <strong>Store:</strong>
                {safe_store}
            </p>

            <p>
                <strong>Previous price:</strong>
                {money(previous_price)}
            </p>

            <p>
                <strong>Current price:</strong>
                {money(current_price)}
            </p>

            <p>
                <strong>Change:</strong>
                {signed_money(change_amount)}
            </p>

            <p>
                <strong>Your target:</strong>
                {money(target_price)}
            </p>
        """

    html = f"""
    <div
        style="
            font-family: Arial, Helvetica, sans-serif;
            max-width: 620px;
            margin: 0 auto;
            padding: 24px;
            color: #1f1f1f;
        "
    >

        <h2
            style="
                margin: 0 0 22px 0;
                font-size: 25px;
            "
        >
            {heading}
        </h2>

        <p
            style="
                font-size: 16px;
                line-height: 1.6;
            "
        >
            {intro}
        </p>

        <div
            style="
                padding: 22px;
                border: 1px solid #dddddd;
                border-radius: 12px;
                margin: 24px 0;
                background: #ffffff;
            "
        >
            {detail_rows}
        </div>

        <p style="margin: 28px 0;">
            <a
                href="{safe_url}"
                style="
                    display: inline-block;
                    padding: 14px 22px;
                    background: #20e6a8;
                    color: #00110d;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: bold;
                "
            >
                View Product
            </a>
        </p>

        <p
            style="
                color: #777777;
                margin-top: 36px;
                font-size: 14px;
            "
        >
            Wishlist found this price because
            you're tracking this product.
        </p>

    </div>
    """

    params: resend.Emails.SendParams = {
        "from": ALERT_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    return resend.Emails.send(
        params
    )


# ============================================================
# SAVED PRODUCT ALERT
# ============================================================

def send_product_alert(
    to_email: str,
    product: dict,
):
    current_price = product.get(
        "currentPrice"
    )

    if current_price is None:
        raise ValueError(
            "Cannot send alert because currentPrice is missing."
        )

    reason = product.get(
        "notificationReason"
    ) or "TARGET_REACHED"

    return send_price_alert(
        to_email=to_email,

        product_name=(
            product.get(
                "displayName"
            )
            or product.get(
                "name"
            )
            or "Tracked product"
        ),

        store=(
            product.get(
                "store"
            )
            or "Unknown store"
        ),

        current_price=float(
            current_price
        ),

        target_price=(
            product.get(
                "targetPrice"
            )
        ),

        previous_price=(
            product.get(
                "previousPrice"
            )
        ),

        product_url=(
            product.get(
                "url"
            )
            or "https://wish-list.com.au"
        ),

        reason=reason,
    )


# ============================================================
# DIGEST PRODUCT CARD
# ============================================================

def build_digest_product_card(
    product: dict,
    changed: bool,
):
    name = escape(
        product.get(
            "displayName"
        )
        or product.get(
            "name"
        )
        or "Tracked product"
    )

    store = escape(
        product.get(
            "store"
        )
        or "Unknown store"
    )

    url = escape(
        product.get(
            "url"
        )
        or "https://wish-list.com.au"
    )

    current_price = product.get(
        "currentPrice"
    )

    target_price = product.get(
        "targetPrice"
    )

    target_difference = None

    if (
        current_price is not None
        and target_price is not None
    ):
        target_difference = round(
            float(current_price)
            - float(target_price),
            2,
        )

    latest_change = product.get(
        "_digestLatestChange"
    )

    if latest_change:

        previous_price = (
            latest_change.get(
                "previousPrice"
            )
        )

        new_price = (
            latest_change.get(
                "currentPrice"
            )
        )

        change_amount = None

        if (
            previous_price is not None
            and new_price is not None
        ):
            change_amount = round(
                float(new_price)
                - float(previous_price),
                2,
            )

        change_text = (
            f"""
            <div
                style="
                    margin-top: 12px;
                    padding: 10px 12px;
                    border-radius: 8px;
                    background: #ecfff8;
                    color: #006d4c;
                    font-weight: 700;
                "
            >
                Price changed:
                {money(previous_price)}
                →
                {money(new_price)}
                &nbsp;
                ({signed_money(change_amount)})
            </div>
            """
        )

    else:

        change_text = """
        <div
            style="
                margin-top: 12px;
                color: #888888;
                font-size: 14px;
            "
        >
            No price change recorded this period.
        </div>
        """

    status_label = (
        "PRICE CHANGED"
        if changed
        else "UNCHANGED"
    )

    status_colour = (
        "#00a875"
        if changed
        else "#888888"
    )

    return f"""
    <div
        style="
            padding: 18px;
            margin-bottom: 14px;
            border: 1px solid #e4e4e4;
            border-radius: 12px;
            background: #ffffff;
        "
    >

        <div
            style="
                font-size: 11px;
                letter-spacing: 1px;
                font-weight: 800;
                color: {status_colour};
                margin-bottom: 7px;
            "
        >
            {status_label}
        </div>

        <div
            style="
                font-size: 18px;
                font-weight: 800;
            "
        >
            {name}
        </div>

        <div
            style="
                color: #777777;
                margin-top: 3px;
            "
        >
            {store}
        </div>

        <table
            style="
                width: 100%;
                margin-top: 16px;
                border-collapse: collapse;
            "
        >
            <tr>
                <td style="padding: 5px 0;">
                    Current price
                </td>

                <td
                    style="
                        padding: 5px 0;
                        text-align: right;
                        font-weight: 700;
                    "
                >
                    {money(current_price)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px 0;">
                    Target price
                </td>

                <td
                    style="
                        padding: 5px 0;
                        text-align: right;
                        font-weight: 700;
                    "
                >
                    {money(target_price)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px 0;">
                    To target
                </td>

                <td
                    style="
                        padding: 5px 0;
                        text-align: right;
                        font-weight: 700;
                    "
                >
                    {signed_money(
                        target_difference
                    )}
                </td>
            </tr>
        </table>

        {change_text}

        <div style="margin-top: 16px;">
            <a
                href="{url}"
                style="
                    color: #00a875;
                    font-weight: 700;
                    text-decoration: none;
                "
            >
                View product →
            </a>
        </div>

    </div>
    """


# ============================================================
# SEND DIGEST EMAIL
# ============================================================

def send_digest_email(
    to_email: str,
    cadence: str,
    products: list[dict],
    content_mode: str,
):
    configure_resend()

    cadence = cadence.upper()

    if cadence == "DAILY_DIGEST":
        digest_name = "Daily"
        subject = "Your daily Wishlist price summary"
        heading = "Your daily Wishlist"
    else:
        digest_name = "Weekly"
        subject = "Your weekly Wishlist price summary"
        heading = "Your weekly Wishlist"

    changed_count = sum(
        1
        for product in products
        if product.get(
            "_digestChanged"
        )
    )

    cards = "".join(
        build_digest_product_card(
            product,
            bool(
                product.get(
                    "_digestChanged"
                )
            ),
        )
        for product in products
    )

    html = f"""
    <div
        style="
            font-family: Arial, Helvetica, sans-serif;
            max-width: 680px;
            margin: 0 auto;
            padding: 26px;
            background: #f7faf9;
            color: #1e2422;
        "
    >

        <div
            style="
                background: #ffffff;
                border-radius: 16px;
                padding: 26px;
                margin-bottom: 18px;
            "
        >

            <div
                style="
                    color: #00a875;
                    font-size: 12px;
                    font-weight: 800;
                    letter-spacing: 1.5px;
                "
            >
                {digest_name.upper()} PRICE SUMMARY
            </div>

            <h1
                style="
                    margin: 10px 0 8px;
                    font-size: 29px;
                "
            >
                {heading}
            </h1>

            <p
                style="
                    margin: 0;
                    color: #6f7774;
                    line-height: 1.6;
                "
            >
                {len(products)} products shown ·
                {changed_count} changed during this period
            </p>

        </div>

        {cards}

        <div
            style="
                text-align: center;
                color: #8a928f;
                font-size: 13px;
                padding: 22px 0;
            "
        >
            Wishlist · Track. Compare. Save.
            <br>
            wish-list.com.au
        </div>

    </div>
    """

    params: resend.Emails.SendParams = {
        "from": ALERT_FROM_EMAIL,
        "to": [to_email],
        "subject": subject,
        "html": html,
    }

    return resend.Emails.send(
        params
    )


# ============================================================
# MANUAL BASIC EMAIL TEST
# ============================================================

def send_test_email():
    if not TEST_ALERT_EMAIL:
        raise RuntimeError(
            "TEST_ALERT_EMAIL is missing. Add it to backend/.env"
        )

    return send_price_alert(
        to_email=TEST_ALERT_EMAIL,

        product_name=(
            "Makita 18V 330mm Lawn Mower Kit"
        ),

        store="Bunnings",

        current_price=357.00,

        target_price=400.00,

        product_url=(
            "https://www.bunnings.com.au/"
        ),

        reason="TARGET_REACHED",
    )


if __name__ == "__main__":
    result = send_test_email()
    print(result)