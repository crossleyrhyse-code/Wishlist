import json
import time
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parent / "comparison_cache.json"
SUCCESS_TTL = 15 * 60
FAILURE_TTL = 5 * 60

def _load():
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}

def _save(data):
    temp = CACHE_FILE.with_suffix(".tmp")
    temp.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temp.replace(CACHE_FILE)

def _key(store, search_text):
    return f"{store.strip().lower()}::{search_text.strip().lower()}"

def get_cached(store, search_text):
    item = _load().get(_key(store, search_text))
    if not isinstance(item, dict) or time.time() >= item.get("expires_at", 0):
        return None
    return item

def cache_success(store, search_text, results):
    data = _load()
    data[_key(store, search_text)] = {
        "status": "ok", "results": results,
        "expires_at": time.time() + SUCCESS_TTL
    }
    _save(data)

def cache_failure(store, search_text, message):
    data = _load()
    data[_key(store, search_text)] = {
        "status": "unavailable", "message": message,
        "expires_at": time.time() + FAILURE_TTL
    }
    _save(data)
