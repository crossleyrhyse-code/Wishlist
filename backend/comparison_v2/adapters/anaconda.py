from __future__ import annotations
from urllib.parse import quote_plus
import requests

from .queueit import QueueItActive, detect_queue_it

BASE = "https://www.anacondastores.com"
SEARCH = BASE + "/search?q={query}"

class AnacondaUnavailable(RuntimeError):
    pass

class AnacondaNoResults(RuntimeError):
    pass

def search_anaconda(query, limit=30, timeout=20):
    """Safe Anaconda entry point.

    While Queue-it is active we stop at the wall. We deliberately do not
    follow the queue, replay tokens, or attempt to bypass it.

    Normal Anaconda catalogue parsing remains intentionally disabled until
    the waiting room is down and its ordinary search response can be proven.
    """
    url = SEARCH.format(query=quote_plus(str(query or "").strip()))
    try:
        r = requests.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 Chrome/153 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml",
            },
            timeout=timeout,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise AnacondaUnavailable(f"Anaconda request failed: {exc}") from exc

    detection = detect_queue_it(
        url=r.url,
        location=r.headers.get("Location"),
        headers=r.headers,
        body=r.text[:250000] if r.text else "",
    )
    if detection.active:
        raise QueueItActive(
            "Anaconda is temporarily using a Queue-it waiting room. "
            "Wishlist backed off and will try again on a later check."
        )

    if 300 <= r.status_code < 400:
        raise AnacondaUnavailable(
            f"Anaconda returned an unexpected redirect (HTTP {r.status_code})."
        )
    if r.status_code != 200:
        raise AnacondaUnavailable(f"Anaconda HTTP {r.status_code}.")

    # We have never yet observed/proven the normal post-queue catalogue page.
    # Do not guess selectors or prices. This state tells us the queue is down
    # and discovery can safely continue in the next retailer phase.
    raise AnacondaUnavailable(
        "Anaconda waiting room is not active, but normal catalogue parsing "
        "has not yet been proven."
    )
