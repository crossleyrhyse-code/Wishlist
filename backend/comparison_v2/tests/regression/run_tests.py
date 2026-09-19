from .fixtures import TEST_CASES
from .parser_fixtures import PARSER_CASES
from ...core.matcher import compare_products
from ...core.parser import parse_product

def run():
    parser_fail=[]
    for c in PARSER_CASES:
        p=parse_product(c["title"])
        bad={k:(getattr(p,k),v) for k,v in c["expected"].items() if getattr(p,k)!=v}
        ok=not bad
        print(f'{"PASS" if ok else "FAIL"} | PARSER | {c["name"]}' + (f" | {bad}" if bad else ""))
        if bad: parser_fail.append((c,bad))

    match_fail=[]
    for c in TEST_CASES:
        r=compare_products(parse_product(c["tracked"]),parse_product(c["candidate"]))
        ok=r.classification==c["expected"]
        print(f'{"PASS" if ok else "FAIL"} | MATCHER | {c["name"]} | expected={c["expected"]} got={r.classification} score={r.score}')
        if not ok: match_fail.append((c,r))

    total=len(PARSER_CASES)+len(TEST_CASES)
    failed=len(parser_fail)+len(match_fail)
    print(f"\nPARSER: {len(PARSER_CASES)-len(parser_fail)}/{len(PARSER_CASES)} passed")
    print(f"MATCHER: {len(TEST_CASES)-len(match_fail)}/{len(TEST_CASES)} passed")
    print(f"TOTAL: {total-failed}/{total} passed")
    if failed: raise SystemExit(1)

if __name__=="__main__": run()
