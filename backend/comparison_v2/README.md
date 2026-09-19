# Wishlist Comparison V2

Comparison V2 is the production comparison engine for Wishlist.

## Production integration

- The user-facing page remains `/compare` and keeps the established polished UI.
- `backend/comparison_routes.py` is a thin compatibility/presentation layer over this engine.
- `/compare-v2` remains available as the direct V2 API used by regression/API tests.
- Same-store alternatives are supported.
- REJECT candidates are never shown as normal customer results.
- Retailer failures are isolated so one unavailable store does not cancel the whole comparison.
- Anaconda Queue-it is reported cleanly as `QUEUE_ACTIVE`; no bypass is attempted.

## Production retailers

- Bunnings
- BCF
- Supercheap Auto
- 4WD Supacentre
- KickAss Products
- Anaconda
- JB Hi-Fi

Kmart is intentionally not registered or shown in the UI because its production adapter is not complete.

## Architecture

1. Product parser -> `ProductProfile`
2. Retailer adapters -> normalized `RetailerProduct`
3. Matching engine -> EXACT / SIMILAR / POSSIBLE / REJECT
4. Price/savings calculation
5. API/UI presentation

## Regression baseline

The parser/matcher master suite is currently 501/501. Run:

```powershell
.\.venv\Scripts\python.exe -m comparison_v2.tests.regression.run_tests
```

API regression:

```powershell
.\.venv\Scripts\python.exe -m comparison_v2.tests.regression.test_api_offline
```

Full live multi-retailer developer test:

```powershell
.\.venv\Scripts\python.exe -m comparison_v2.tests.live.test_compare_all "PRODUCT TITLE" --price 100 --limit 20
```

## Retailer expansion

Retailer expansion is parked during beta preparation. New retailers should be developed and proven in live tests before being added to `RETAILERS`; unsupported/unfinished retailers must not be surfaced in the customer UI.
