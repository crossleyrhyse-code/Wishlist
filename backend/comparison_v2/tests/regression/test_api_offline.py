from fastapi import FastAPI
from fastapi.testclient import TestClient
from ...core import engine as ce
from ...api_routes import router
from ...core.retailer_product import RetailerProduct

def run():
    original=dict(ce.RETAILERS)
    try:
        def good(query,limit=20):
            return [
                RetailerProduct("BCF","XTM 270° 2m Awning","https://example/xtm",599.0,"$599.00"),
                RetailerProduct("BCF","XTM Mighty 270° Awning Wall Kit","https://example/wall",299.99,"$299.99"),
            ]
        class Down(RuntimeError): pass
        def down(query,limit=20): raise Down("test outage")
        ce.RETAILERS={"BCF":(good,RuntimeError),"Bunnings":(down,Down)}

        app=FastAPI()
        app.include_router(router)
        client=TestClient(app)
        r=client.post("/compare-v2",json={
            "title":"Kings Plus 270 Degree Tourer XL Freestanding Awning MKII",
            "price":849,
            "query":"270 degree awning"
        })
        assert r.status_code==200
        data=r.json()
        assert data["tracked_price"]==849
        assert len(data["results"])==1
        assert data["results"][0]["retailer"]=="BCF"
        assert data["results"][0]["classification"]=="SIMILAR"
        assert data["results"][0]["price"]==599
        assert data["results"][0]["savings"]==250
        assert data["rejected_count"]==1
        assert data["retailers"][1]["available"] is False

        bad=client.post("/compare-v2",json={
            "title":"Camping Chair","retailers":["NotAStore"]
        })
        assert bad.status_code==400
        print("API: 9/9 passed")
    finally:
        ce.RETAILERS=original

if __name__=="__main__":
    run()
