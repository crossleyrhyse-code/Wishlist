from __future__ import annotations
from dataclasses import dataclass
from urllib.parse import urlparse

@dataclass(frozen=True)
class QueueItDetection:
    active: bool
    reason: str | None = None

def detect_queue_it(*, url: str | None = None, location: str | None = None,
                    headers=None, body: str | None = None) -> QueueItDetection:
    """Conservative Queue-it waiting-room detection.

    This only detects and reports the wall. It never follows/manufactures
    queue tokens or attempts to bypass the waiting room.
    """
    urls = [str(x or "") for x in (url, location)]
    hosts = []
    for value in urls:
        try:
            hosts.append((urlparse(value).hostname or "").lower())
        except Exception:
            pass

    if any(h == "queue-it.net" or h.endswith(".queue-it.net")
           or h.startswith("queue.") for h in hosts):
        return QueueItDetection(True, "Queue-it waiting room redirect detected.")

    h = {str(k).lower(): str(v).lower() for k, v in (headers or {}).items()}
    location_header = h.get("location", "")
    if "queue-it" in location_header or "queueittoken" in location_header:
        return QueueItDetection(True, "Queue-it waiting room redirect detected.")

    text = str(body or "").lower()
    strong_markers = (
        "queue-it",
        "queueittoken",
        "waiting room",
        "you are now in line",
        "estimated wait time",
    )
    if sum(marker in text for marker in strong_markers) >= 2:
        return QueueItDetection(True, "Queue-it waiting room page detected.")

    return QueueItDetection(False)

class QueueItActive(RuntimeError):
    pass
