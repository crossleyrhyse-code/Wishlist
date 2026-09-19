# Wishlist Comparison V2

Stable seven-retailer baseline before the next retailer-expansion phase.

## Structure

- `adapters/` — one retailer adapter per store plus shared Queue-it handling.
- `core/` — parser, matcher, normalized retailer product model, and multi-retailer engine.
- `tests/regression/` — permanent offline safety/regression tests.
- `tests/live/` — developer-facing live retailer tests.
- `api_routes.py` / `api_models.py` — FastAPI boundary.

Temporary discovery scripts, captured debug data, Python caches, and superseded development files are deliberately excluded.

## Registered retailers

1. Bunnings
2. BCF
3. Supercheap Auto
4. 4WD Supacentre
5. KickAss Products
6. Anaconda
7. JB Hi-Fi

Anaconda can legitimately report `QUEUE_ACTIVE` when its Queue-it waiting room is active. Wishlist backs off rather than attempting to bypass it.

## Baseline status

At this checkpoint:

- Master parser/matcher regression: 501/501 passing.
- Final focused bugfix regression: 7/7 passing.
- Cross-category entertainment/merchandise false positives from the Makita Chainsaw live test are rejected.
- Supercheap long-title fallback is working for the Kings 270-degree awning test.
- Retailer failures are isolated so one unavailable retailer does not stop the full comparison run.

## Retailer onboarding workflow

For each new retailer:

1. Build the retailer adapter and normalize its output.
2. Verify product discovery and price extraction.
3. Run several different real products through PowerShell.
4. Inspect returned products AND their EXACT / SIMILAR / POSSIBLE / REJECT classifications.
5. Fix retailer-specific retrieval problems inside the adapter.
6. Fix core parser/matcher behavior only when the failure is genuinely generic.
7. Add permanent regression coverage for real failures.
8. Re-run the baseline regression suite.
9. Freeze the retailer and move to the next store.

This PowerShell-first workflow remains the preferred development path until most launch retailers are onboarded. The polished Wishlist comparison UI will be integrated after the comparison base is broad and stable.

## Useful commands

Master parser/matcher regression:

`python -m comparison_v2.tests.regression.run_tests`

Focused final bugfix regression:

`python -m comparison_v2.tests.regression.test_final_bugfix`

Live all-retailer check:

`python -m comparison_v2.tests.live.test_compare_all "<product title>" --price <price> --limit 20`

## Next retailer expansion queue

Kmart, BIG W, Repco, Autobarn, Target, Harvey Norman, The Good Guys, Fantastic Furniture, Amart Furniture, then Amazon Australia.
