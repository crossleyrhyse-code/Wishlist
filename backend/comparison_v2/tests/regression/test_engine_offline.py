from ...core import engine as ce
from ...core.retailer_product import RetailerProduct

def run():
    original=dict(ce.RETAILERS)
    try:
        def good(query,limit=20):
            return [
                RetailerProduct("FakeGood","Kings Plus 270 Degree Tourer XL Freestanding Awning MKII","https://example/a",849.0,"$849.00"),
                RetailerProduct("FakeGood","XTM Mighty 270° 2.5m Awning","https://example/b",799.0,"$799.00"),
                RetailerProduct("FakeGood","XTM Mighty 270° Awning Wall Kit","https://example/c",299.99,"$299.99"),
            ]
        class Down(RuntimeError): pass
        def down(query,limit=20): raise Down("test outage")
        ce.RETAILERS={"Good":(good,RuntimeError),"Down":(down,Down)}
        r=ce.compare_across_retailers(
            "Kings Plus 270 Degree Tourer XL Freestanding Awning MKII",
            tracked_price=849, query="270 degree awning"
        )
        assert len(r.results)==2, len(r.results)
        assert len(r.rejected)==1, len(r.rejected)
        assert r.results[0].classification=="EXACT"
        assert r.results[1].classification=="SIMILAR"
        assert r.results[1].savings==50.0
        assert r.retailers[0].available is True
        assert r.retailers[1].available is False
        print("ENGINE: 8/8 passed")
    finally:
        ce.RETAILERS=original

if __name__=="__main__": run()
