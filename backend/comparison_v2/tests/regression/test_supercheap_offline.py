from ...adapters.supercheap import _parse_search_html


def _tile(title, url, sale=None, standard=None, member=None):
    pricing = '<div class="product-pricing">'
    if sale is not None:
        pricing += (
            '<span class="product-sales-price has-standard-price" title="Sale Price">'
            f'<span class="sp-nowrap"><span class="the-price">${sale}</span></span></span>'
        )
    if standard is not None:
        pricing += (
            '<span class="product-standard-price" title="Standard Price">'
            f'<span class="sp-nowrap"><span class="the-price">${standard}</span></span></span>'
        )
    if member is not None:
        pricing += (
            '<div class="member-price"><span class="txt-price">'
            f'${member}</span><span class="txt-member">Member</span></div>'
        )
    pricing += "</div>"
    return (
        '<li class="grid-tile"><div class="product-tile">'
        '<div class="product-name">'
        f'<a class="name-link" href="{url}" title="Go to Product: {title}">{title}</a>'
        '</div>'
        + pricing
        + '</div></li>'
    )


def main():
    html = (
        _tile(
            "ToolPRO Auto Diagnostic Scanner OBD2 and CAN",
            "/p/toolpro-toolpro-auto-diagnostic-scanner-obd2-and-can/590595.html",
            sale="83.99",
            standard="142.99",
        )
        + _tile(
            "SCA Auto Diagnostic Scanner",
            "/p/sca-sca-auto-diagnostic-scanner/732579.html",
            standard="49.99",
        )
        + _tile(
            "Member Price Test",
            "/p/test/member-price-test/123456.html",
            standard="100.00",
            member="80.00",
        )
        + _tile(
            "No Public Price",
            "/p/test/no-public-price/654321.html",
            member="70.00",
        )
    )

    products = _parse_search_html(html)
    assert len(products) == 4

    first = products[0]
    assert first.retailer == "Supercheap Auto"
    assert first.title == "ToolPRO Auto Diagnostic Scanner OBD2 and CAN"
    assert first.url == "https://www.supercheapauto.com.au/p/toolpro-toolpro-auto-diagnostic-scanner-obd2-and-can/590595.html"
    assert first.price == 83.99
    assert first.price_text == "$83.99"

    assert products[1].price == 49.99
    assert products[2].price == 100.00   # standard, not member price
    assert products[3].price is None     # member-only price is not substituted

    print("SUPERCHEAP TILE/PUBLIC PRICE: 10/10 passed")


if __name__ == "__main__":
    main()
