from ...core.parser import parse_product
from ...core.matcher import compare_products
from ...adapters.supercheap import _fallback_queries


def _classification(tracked, candidate):
    return compare_products(parse_product(tracked), parse_product(candidate)).classification


def main():
    cases = [
        ("Makita Chainsaw", "Chainsaw Man - Denji Poster", "REJECT"),
        ("Makita Chainsaw", "Chainsaw Man - Yum Yum Poster", "REJECT"),
        ("Makita Chainsaw", "Texas Chainsaw Massacre (Original Motion Picture Score)(Australian Exclusive Rust/Blood Red Vinyl)", "REJECT"),
        ("Makita Chainsaw", 'Makita 18V 10" 250mm Brushless Chainsaw DUC254Z - Skin Only', "NOT_REJECT"),
        ("Chair", "Marquee Padded Vinyl Black Folding Chair", "NOT_REJECT"),
    ]

    passed = 0
    for tracked, candidate, expected in cases:
        got = _classification(tracked, candidate)
        ok = got == "REJECT" if expected == "REJECT" else got != "REJECT"
        print(f"{'PASS' if ok else 'FAIL'}: {candidate!r} -> {got}")
        assert ok, f"{candidate!r}: expected {expected}, got {got}"
        passed += 1

    q = "Kings Plus 270° Tourer XL Freestanding Awning MKII"
    fallbacks = _fallback_queries(q)
    assert fallbacks == ["270 awning", "awning"], fallbacks
    print(f"PASS: Supercheap fallback queries -> {fallbacks}")
    passed += 1

    assert _fallback_queries("Makita Chainsaw") == []
    print("PASS: unrelated searches do not gain speculative Supercheap fallbacks")
    passed += 1

    print(f"FINAL BUGFIX: {passed}/{passed} passed")


if __name__ == "__main__":
    main()
