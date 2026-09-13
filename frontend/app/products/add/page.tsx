"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { addWishlistProduct } from "../../data/wishlistProducts";
const API_BASE_URL = "http://127.0.0.1:8000";

type AnalysedProduct = {
  url: string;
  store: string;
  title: string;
  currentPrice: number;
  imageUrl: string | null;
};

function money(value: number) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

function inferCategory(title: string) {
  const text = title.toLowerCase();

  if (
    text.includes("drill") ||
    text.includes("chainsaw") ||
    text.includes("shovel") ||
    text.includes("blower") ||
    text.includes("tool")
  ) {
    return "Tools & DIY";
  }

  if (
    text.includes("chair") ||
    text.includes("awning") ||
    text.includes("tent") ||
    text.includes("reel") ||
    text.includes("camp")
  ) {
    return "Sports & Outdoors";
  }

  if (
    text.includes("headphone") ||
    text.includes("speaker") ||
    text.includes("tv") ||
    text.includes("phone") ||
    text.includes("laptop")
  ) {
    return "Electronics";
  }

  if (text.includes("food") || text.includes("grocery")) {
    return "Groceries";
  }

  return "Other";
}

export default function AddProductPage() {
  const [url, setUrl] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [notes, setNotes] = useState("");
  const [analysedProduct, setAnalysedProduct] =
    useState<AnalysedProduct | null>(null);
  const [analysing, setAnalysing] = useState(false);
  const [adding, setAdding] = useState(false);
  const [added, setAdded] = useState(false);
  const [error, setError] = useState("");

  async function analyseProduct(event: FormEvent) {
    event.preventDefault();

    if (!url.trim()) return;

    setAnalysing(true);
    setAdded(false);
    setError("");
    setAnalysedProduct(null);

    try {
      const response = await fetch(`${API_BASE_URL}/analyse-product`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim() }),
      });

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || "Could not analyse this product.");
      }

      setAnalysedProduct({
        url: result.url,
        store: result.store,
        title: result.title,
        currentPrice: result.currentPrice,
        imageUrl: result.imageUrl,
      });
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not analyse this product.",
      );
    } finally {
      setAnalysing(false);
    }
  }

  async function addProduct() {
    if (!analysedProduct) return;

    setAdding(true);
    setAdded(false);
    setError("");

    try {
      const parsedTargetPrice =
        targetPrice.trim() === "" ? null : Number(targetPrice);

      if (
        parsedTargetPrice !== null &&
        (!Number.isFinite(parsedTargetPrice) || parsedTargetPrice < 0)
      ) {
        throw new Error("Target price must be a valid positive number.");
      }

      await addWishlistProduct({
        url: analysedProduct.url,
        displayName: analysedProduct.title,
        store: analysedProduct.store,
        category: inferCategory(analysedProduct.title),
        currentPrice: analysedProduct.currentPrice,
        imageUrl: analysedProduct.imageUrl,
        targetPrice: parsedTargetPrice,
        notes: notes.trim() || null,
      });

      setAdded(true);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not add this product.",
      );
    } finally {
      setAdding(false);
    }
  }

  return (
<section className="add-product-dashboard">
        <header className="add-product-header">
          <div>
            <span className="eyebrow">START TRACKING</span>
            <h2>Add Product</h2>
            <p>Paste a product link and Wishlist will do the rest.</p>
          </div>

          <Link href="/products" className="secondary-page-button">
            ‹ My Products
          </Link>
        </header>

        <div className="add-product-layout">
          <section className="glass-card add-product-card">
            <div className="add-step-heading">
              <span className="step-number">1</span>
              <div>
                <h3>Paste a product link</h3>
                <p>Copy the URL from the retailer&apos;s product page.</p>
              </div>
            </div>

            <form className="product-url-form" onSubmit={analyseProduct}>
              <label htmlFor="product-url">PRODUCT URL</label>

              <div className="product-url-row">
                <input
                  id="product-url"
                  type="url"
                  placeholder="https://www.example.com/product..."
                  value={url}
                  onChange={(event) => setUrl(event.target.value)}
                  required
                />

                <button type="submit" disabled={analysing}>
                  {analysing ? "Analysing..." : "Analyse Product"}
                </button>
              </div>

              <small>
                Wishlist will check the retailer page for the real product name,
                image and current price.
              </small>
            </form>

            {error && (
              <div className="product-added-message">
                <span>!</span>
                <div>
                  <strong>Wishlist hit a problem.</strong>
                  <p>{error}</p>
                </div>
              </div>
            )}

            <div className="supported-store-strip">
              <span>Built around the stores we&apos;ve already worked with:</span>
              <div>
                <b>Bunnings</b>
                <b>BCF</b>
                <b>Supercheap Auto</b>
                <b>Anaconda</b>
                <b>4WD Supacentre</b>
                <b>KickAss Products</b>
              </div>
            </div>
          </section>

          <aside className="glass-card add-help-card">
            <span className="eyebrow">HOW IT WORKS</span>
            <h3>Paste. Check. Track.</h3>

            <ol>
              <li>Paste the retailer&apos;s product URL.</li>
              <li>Wishlist finds the name, image and current price.</li>
              <li>Set an optional target price.</li>
              <li>Add it to My Products and Wishlist starts tracking it.</li>
            </ol>

            <div className="future-note">
              <strong>Live backend connected</strong>
              <span>
                Product analysis and saving now run through the Python Wishlist
                backend.
              </span>
            </div>
          </aside>
        </div>

        {analysedProduct && (
          <section className="glass-card product-preview-card">
            <div className="add-step-heading">
              <span className="step-number">2</span>
              <div>
                <h3>Product found</h3>
                <p>Check the details before adding it to your Wishlist.</p>
              </div>
            </div>

            <div className="product-preview-body">
              <div className="preview-product-image">
                {analysedProduct.imageUrl ? (
                  <img
                    src={analysedProduct.imageUrl}
                    alt={analysedProduct.title}
                    referrerPolicy="no-referrer"
                    style={{
                      width: "100%",
                      height: "100%",
                      objectFit: "contain",
                      borderRadius: "inherit",
                    }}
                  />
                ) : (
                  <span>◫</span>
                )}
              </div>

              <div className="preview-product-main">
                <span className="preview-store">
                  {analysedProduct.store.toUpperCase()} ·{" "}
                  {inferCategory(analysedProduct.title).toUpperCase()}
                </span>

                <h3>{analysedProduct.title}</h3>
                <p className="preview-url">{analysedProduct.url}</p>

                <div className="preview-price-line">
                  <div>
                    <span>CURRENT PRICE</span>
                    <strong>{money(analysedProduct.currentPrice)}</strong>
                  </div>

                  <div>
                    <span>STORE</span>
                    <strong>{analysedProduct.store}</strong>
                  </div>

                  <div>
                    <span>STATUS</span>
                    <strong className="preview-status">Ready to track</strong>
                  </div>
                </div>
              </div>
            </div>

            <div className="tracking-options">
              <label>
                <span>
                  TARGET PRICE <small>(optional)</small>
                </span>

                <div className="money-input">
                  <b>$</b>
                  <input
                    type="number"
                    min="0"
                    step="0.01"
                    placeholder="400.00"
                    value={targetPrice}
                    onChange={(event) => setTargetPrice(event.target.value)}
                  />
                </div>
              </label>

              <label>
                <span>
                  NOTES <small>(optional)</small>
                </span>

                <input
                  type="text"
                  placeholder="e.g. Wait for a sale before buying"
                  value={notes}
                  onChange={(event) => setNotes(event.target.value)}
                />
              </label>

              <button
                className="confirm-add-button"
                onClick={addProduct}
                disabled={adding || added}
              >
                {adding
                  ? "Adding..."
                  : added
                    ? "✓ Added to Wishlist"
                    : "＋ Add to Wishlist"}
              </button>
            </div>

            {added && (
              <div className="product-added-message">
                <span>✓</span>
                <div>
                  <strong>Product added to Wishlist.</strong>
                  <p>
                    It is now saved in the backend and will appear in My
                    Products.
                  </p>
                </div>
              </div>
            )}
          </section>
        )}

        <footer className="dashboard-footer">
          <span>© 2026 Wishlist. Pick a WishList. Get a Bargain.</span>
          <div>
            <button>Privacy</button>
            <button>Help</button>
          </div>
        </footer>
      </section>
);
}