from comparison_v2.core.parser import parse_product
from comparison_v2.core.matcher import compare_products

CASES = [
    # Bug 1: franchise/collectible titles must not compare as physical chainsaws.
    ("Makita Chainsaw", "Chainsaw Man - Makima Pop! Vinyl", "REJECT"),
    ("Makita Chainsaw", "Chainsaw Man: Perching Figure Makima Figure", "REJECT"),
    ("Makita Chainsaw", "Chainsaw Man: Noodle Stopper Figure - Makima Figure", "REJECT"),
    ("Makita Chainsaw", "Nendoroid: Chainsaw Man - Makima", "REJECT"),
    ("Makita Chainsaw", "Lookup Chainsaw Man Makima (Repeat)", "REJECT"),

    # Bug 2: chair add-ons must not compare as complete chairs.
    ("Chair", "Charli Chair Seat Pad Black Cushion", "REJECT"),
    ("Chair", "Front Runner Expander Chair Side Table - TBRA052", "REJECT"),

    # Guard rails: genuine products must still survive.
    ("Makita Chainsaw", 'Makita 18V 10" 250mm Brushless Chainsaw DUC254Z - Skin Only', "NOT_REJECT"),
    ("Chair", "Ridge Ryder Nullabor Camp Chair", "NOT_REJECT"),
    ("Chair", "Oztent Gecko Camping Chair - With Side Table", "NOT_REJECT"),
    ("Chair", "Ridge Ryder Premium Arm Cooler with Wine Holder Chair", "NOT_REJECT"),
]

passed = 0
for tracked_title, candidate_title, expected in CASES:
    tracked = parse_product(tracked_title)
    candidate = parse_product(candidate_title)
    result = compare_products(tracked, candidate)

    ok = (result.classification == "REJECT") if expected == "REJECT" else (result.classification != "REJECT")
    status = "PASS" if ok else "FAIL"
    print(f"{status}: {tracked_title!r} vs {candidate_title!r} -> {result.classification} {result.score}%")
    if not ok:
        raise AssertionError(
            f"Expected {expected}, got {result.classification} for {candidate_title!r}. Reasons: {result.reasons}"
        )
    passed += 1

print(f"BUGFIX PRODUCT CONTEXT: {passed}/{len(CASES)} passed")
