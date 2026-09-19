"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { loadWishlistProducts } from "../data/wishlistProducts";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

type WishlistProduct = {
  id: string;
  name: string;
  displayName: string;
  store: string;
  category: string;
  url: string;
  targetPrice: number | null;
  imageUrl: string | null;
  currentPrice: number | null;
};

type MatchType = "EXACT MATCH" | "SIMILAR PRODUCT" | "POSSIBLE MATCH" | "NO MATCH";

type ComparisonCandidate = {
  name: string;
  url: string;
  percentage: number;
  nameScore: number;
  identityScore: number;
  numbersMatch: boolean;
  brandMatch: boolean;
  reasons?: string[];
  matchType: MatchType;
  price: number | null;
  priceError: string | null;
  priceDifference: number | null;
  saving: number | null;
};

type RetailerComparison = {
  store: string;
  searchedCount: number;
  strongestMatch: ComparisonCandidate | null;
  matches: ComparisonCandidate[];
  hasMore: boolean;
  nextOffset: number;
  reason?: string | null;
  error?: string;
};

type ComparisonResponse = {
  success: boolean;
  product: {
    id: string;
    name: string;
    comparisonTitle: string;
    store: string;
    url: string;
    imageUrl: string | null;
    currentPrice: number | null;
    targetPrice: number | null;
  };
  selectedStores: string[];
  retailers: RetailerComparison[];
};


function money(value: number | null) {
  if (value === null) return "—";

  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

function matchClass(matchType: MatchType) {
  if (matchType === "EXACT MATCH") return "exact";
  if (matchType === "SIMILAR PRODUCT") return "similar";
  if (matchType === "POSSIBLE MATCH") return "possible";
  return "no-match";
}

export default function Page() {
  const [products, setProducts] = useState<WishlistProduct[]>([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [result, setResult] = useState<ComparisonResponse | null>(null);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [comparing, setComparing] = useState(false);
  const [error, setError] = useState("");
  const [openRetailers, setOpenRetailers] = useState<Record<string, boolean>>({});
  const [storeMenuOpen, setStoreMenuOpen] = useState(false);
  const [availableCompareStores, setAvailableCompareStores] = useState<string[]>([]);
  const [selectedStores, setSelectedStores] = useState<string[]>([]);
  const [loadingMoreStores, setLoadingMoreStores] = useState<Record<string, boolean>>({});

  useEffect(() => {
    async function loadComparisonPage() {
      try {
        const [productData, storeResponse] = await Promise.all([
          loadWishlistProducts() as Promise<WishlistProduct[]>,
          fetch(`${API_BASE_URL}/compare/stores`, { cache: "no-store" }),
        ]);

        if (!storeResponse.ok) {
          throw new Error("Could not load comparison stores.");
        }

        const storeData = (await storeResponse.json()) as { stores?: string[] };
        const stores = Array.isArray(storeData.stores) ? storeData.stores : [];

        setProducts(productData);
        setAvailableCompareStores(stores);
        setError("");

        if (productData.length > 0) {
          setSelectedProductId(productData[0].id);
          // Comparison V2 intentionally allows same-store alternatives.
          setSelectedStores(stores);
        } else {
          setSelectedProductId("");
          setSelectedStores([]);
          setResult(null);
        }
      } catch (loadError) {
        setProducts([]);
        setAvailableCompareStores([]);
        setSelectedProductId("");
        setSelectedStores([]);
        setResult(null);
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Could not load the comparison page.",
        );
      } finally {
        setLoadingProducts(false);
      }
    }

    loadComparisonPage();
  }, []);

  const selectedProduct = useMemo(
    () =>
      products.find((product) => product.id === selectedProductId) ?? null,
    [products, selectedProductId],
  );

  async function compareSelectedProduct() {
    if (!selectedProductId) return;

    setComparing(true);
    setError("");
    setResult(null);
    setOpenRetailers({});

    try {
      const response = await fetch(
        `${API_BASE_URL}/compare/${selectedProductId}`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            selectedStores,
            product: selectedProduct,
          }),
        },
      );

      const body = await response.json();

      if (!response.ok) {
        throw new Error(
          body?.detail || "Price comparison could not be completed.",
        );
      }

      setResult(body as ComparisonResponse);
    } catch (compareError) {
      setError(
        compareError instanceof Error
          ? compareError.message
          : "Price comparison could not be completed.",
      );
    } finally {
      setComparing(false);
    }
  }

  async function loadMoreMatches(store: string, offset: number) {
    if (!result) return;

    setLoadingMoreStores((current) => ({
      ...current,
      [store]: true,
    }));

    try {
      const response = await fetch(
        `${API_BASE_URL}/compare/${result.product.id}/more/${encodeURIComponent(
          store,
        )}?offset=${offset}&limit=5`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            product: selectedProduct,
          }),
        },
      );

      const body = await response.json();

      if (!response.ok) {
        throw new Error(
          body?.detail || `Could not load more ${store} matches.`,
        );
      }

      setResult((current) => {
        if (!current) return current;

        return {
          ...current,
          retailers: current.retailers.map((retailer) =>
            retailer.store === store
              ? {
                  ...retailer,
                  matches: [...retailer.matches, ...(body.matches ?? [])],
                  hasMore: Boolean(body.hasMore),
                  nextOffset: body.nextOffset ?? retailer.nextOffset,
                }
              : retailer,
          ),
        };
      });
    } catch (loadMoreError) {
      setError(
        loadMoreError instanceof Error
          ? loadMoreError.message
          : `Could not load more ${store} matches.`,
      );
    } finally {
      setLoadingMoreStores((current) => ({
        ...current,
        [store]: false,
      }));
    }
  }

  const sourcePrice =
    result?.product.currentPrice ?? selectedProduct?.currentPrice ?? null;

  const pricedRetailerMatches = useMemo(() => {
    if (!result) return [];

    return result.retailers
      .map((retailer) => ({
        retailer,
        strongest: retailer.strongestMatch,
      }))
      .filter(
        (entry) =>
          entry.strongest?.price !== null &&
          entry.strongest?.price !== undefined,
      )
      .sort(
        (a, b) =>
          (a.strongest?.price ?? Number.POSITIVE_INFINITY) -
          (b.strongest?.price ?? Number.POSITIVE_INFINITY),
      );
  }, [result]);

  const bestComparisonPrice = pricedRetailerMatches[0]?.strongest?.price ?? null;
  const overallBestPrice =
    sourcePrice !== null && bestComparisonPrice !== null
      ? Math.min(sourcePrice, bestComparisonPrice)
      : sourcePrice ?? bestComparisonPrice;

  return (
    <>
      <style jsx global>{`
        .comparison-dashboard {
          min-width: 0;
          color: #0f172a;
        }

        .comparison-dashboard .card,
        .comparison-dashboard .glass-card {
          color: #0f172a;
        }

        .comparison-header {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 24px;
          padding: 28px 32px 18px;
        }

        .comparison-header h2 {
          margin: 4px 0 4px;
          font-size: clamp(32px, 4vw, 52px);
          line-height: 1;
          font-weight: 700;
        }

        .comparison-header p {
          margin: 0;
          color: #64748b;
        }

        .comparison-shell {
          padding: 0 32px 28px;
          display: grid;
          gap: 16px;
        }

        .compare-picker {
          position: relative;
          z-index: 100;
          overflow: visible;
          display: grid;
          grid-template-columns: minmax(0, 1fr) auto;
          gap: 14px;
          padding: 18px;
          align-items: end;
        }

        .compare-picker label {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .compare-picker label span,
        .compare-label {
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: #64748b;
        }

        .compare-select {
          height: 48px;
          width: 100%;
          padding: 0 14px;
          border-radius: 11px;
          border: 1px solid #dbe4ea;
          background: rgba(3, 13, 15, 0.76);
          color: #0f172a;
          font: inherit;
          font-weight: 700;
          outline: none;
        }

        .compare-button {
          height: 48px;
          padding: 0 22px;
          border: 0;
          border-radius: 11px;
          background: var(--mint);
          color: #03110f;
          font-weight: 900;
          cursor: pointer;
          white-space: nowrap;
        }

        .compare-button:disabled {
          opacity: 0.48;
          cursor: not-allowed;
        }


        .compare-action-wrap {
          position: relative;
          z-index: 110;
          overflow: visible;
        }

        .store-picker-popover {
          position: absolute;
          top: calc(100% + 8px);
          right: 0;
          z-index: 9999;
          width: 290px;
          padding: 12px;
          border-radius: 12px;
          border: 1px solid #e2e8f0;
          background: #ffffff;
          box-shadow: 0 18px 40px rgba(15, 23, 42, 0.14);
        }

        .store-picker-title {
          margin-bottom: 8px;
          color: #0f172a;
          font-size: 12px;
          font-weight: 900;
        }

        .store-picker-option {
          min-height: 42px;
          display: grid;
          grid-template-columns: 20px 1fr auto;
          gap: 9px;
          align-items: center;
          padding: 7px 8px;
          border-radius: 8px;
          color: #334155;
          cursor: pointer;
        }

        .store-picker-option:hover {
          background: #f0fdf7;
        }

        .store-picker-option.disabled {
          opacity: 0.5;
          cursor: default;
        }

        .store-picker-option input {
          accent-color: var(--mint);
        }

        .store-picker-option small {
          color: #64748b;
          font-size: 9px;
        }

        .store-picker-run {
          width: 100%;
          min-height: 40px;
          margin-top: 9px;
          border: 0;
          border-radius: 9px;
          background: var(--mint);
          color: #03110f;
          font-weight: 900;
          cursor: pointer;
        }

        .store-picker-run:disabled {
          opacity: 0.45;
          cursor: not-allowed;
        }

        .compare-source-card {
          position: relative;
          z-index: 1;
          display: grid;
          grid-template-columns: 76px minmax(0, 1fr) repeat(2, minmax(110px, 0.45fr));
          gap: 18px;
          align-items: center;
          padding: 18px;
        }

        .compare-product-image {
          width: 76px;
          height: 76px;
          border-radius: 14px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          background: rgba(244, 248, 247, 0.94);
        }

        .compare-product-image img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .compare-product-copy strong {
          display: block;
          margin-bottom: 5px;
          font-size: 18px;
        }

        .compare-product-copy span {
          color: #64748b;
          font-size: 12px;
        }

        .compare-product-copy .compare-label {
          color: #64748b;
          font-weight: 800;
        }

        .compare-metric {
          display: flex;
          flex-direction: column;
          gap: 4px;
        }

        .compare-metric strong {
          font-size: 18px;
        }

        .compare-results-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
          gap: 16px;
        }

        .retailer-card {
          position: relative;
          padding: 20px;
          overflow: hidden;
        }

        .retailer-card.best {
          border-color: rgba(52, 238, 182, 0.45);
          box-shadow: inset 0 0 0 1px rgba(52, 238, 182, 0.08);
        }

        .best-price-ribbon {
          position: absolute;
          top: 14px;
          right: 14px;
          padding: 6px 9px;
          border-radius: 999px;
          background: rgba(52, 238, 182, 0.14);
          border: 1px solid rgba(52, 238, 182, 0.3);
          color: var(--mint);
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .retailer-heading {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 18px;
        }

        .retailer-mark {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(52, 238, 182, 0.1);
          color: var(--mint);
          font-weight: 900;
        }

        .retailer-heading strong {
          display: block;
          font-size: 18px;
        }

        .retailer-heading span {
          color: #64748b;
          font-size: 11px;
        }

        .retailer-price {
          margin: 2px 0 4px;
          font-size: clamp(32px, 4vw, 46px);
          font-weight: 800;
          letter-spacing: -0.04em;
        }

        .retailer-price.mint {
          color: var(--mint);
        }

        .match-badge {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          margin-top: 12px;
          padding: 6px 9px;
          border-radius: 8px;
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.04em;
        }

        .match-badge.exact {
          color: var(--mint);
          background: rgba(52, 238, 182, 0.1);
        }

        .match-badge.similar {
          color: #ffd26f;
          background: rgba(255, 210, 111, 0.1);
        }

        .match-badge.possible {
          color: #f3c66d;
          background: rgba(243, 198, 109, 0.09);
          border: 1px solid rgba(243, 198, 109, 0.18);
        }

        .match-badge.no-match {
          color: #ff8f73;
          background: rgba(255, 143, 115, 0.1);
        }

        .comparison-saving {
          margin-top: 14px;
          padding: 11px 12px;
          border-radius: 10px;
          background: rgba(52, 238, 182, 0.08);
          color: var(--mint);
          font-weight: 800;
        }

        .comparison-warning {
          margin-top: 14px;
          padding: 11px 12px;
          border-radius: 10px;
          background: rgba(255, 143, 115, 0.08);
          color: #ff9b83;
          font-size: 12px;
        }

        .store-link {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          margin-top: 16px;
          min-height: 40px;
          padding: 0 14px;
          border-radius: 9px;
          border: 1px solid #dbe4ea;
          color: #334155;
          text-decoration: none;
          font-weight: 800;
          font-size: 12px;
        }

        .comparison-empty {
          min-height: 260px;
          padding: 34px;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: #64748b;
        }

        .comparison-error {
          padding: 14px 16px;
          border-radius: 11px;
          border: 1px solid rgba(255, 103, 103, 0.24);
          background: rgba(255, 103, 103, 0.08);
          color: #ff9b8d;
        }

        .possible-matches {
          padding: 0;
          overflow: hidden;
        }

        .possible-matches-toggle {
          width: 100%;
          min-height: 52px;
          padding: 0 18px;
          border: 0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: transparent;
          color: #0f172a;
          font: inherit;
          font-weight: 800;
          cursor: pointer;
        }

        .candidate-list {
          border-top: 1px solid #e2e8f0;
        }

        .candidate-row {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 90px 130px auto;
          gap: 14px;
          align-items: center;
          padding: 13px 18px;
          border-bottom: 1px solid #e2e8f0;
        }

        .candidate-row:last-child {
          border-bottom: 0;
        }

        .candidate-copy strong {
          display: block;
          margin-bottom: 3px;
          font-size: 12px;
        }

        .candidate-copy span {
          color: #64748b;
          font-size: 10px;
        }

        .candidate-score {
          color: var(--mint);
          font-weight: 900;
        }


        .comparison-summary-card {
          display: flex;
          align-items: center;
          justify-content: space-between;
          gap: 22px;
          padding: 18px 20px;
        }

        .comparison-summary-card > div:first-child strong {
          display: block;
          margin-top: 5px;
          font-size: 15px;
        }

        .comparison-summary-metrics {
          display: grid;
          grid-template-columns: repeat(3, minmax(110px, 1fr));
          gap: 22px;
        }

        .comparison-summary-metrics div {
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .comparison-summary-metrics span {
          color: #64748b;
          font-size: 10px;
          font-weight: 800;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .comparison-summary-metrics strong {
          font-size: 17px;
        }

        .comparison-summary-metrics .mint {
          color: var(--mint);
        }

        .retailer-stack {
          position: relative;
          z-index: 1;
          display: grid;
          gap: 16px;
        }

        .retailer-primary-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) minmax(150px, 0.32fr) auto;
          gap: 20px;
          align-items: end;
        }

        .retailer-product-title {
          display: block;
          margin-top: 5px;
          max-width: 720px;
          font-size: 17px;
          line-height: 1.35;
        }

        .retailer-price-wrap {
          display: flex;
          flex-direction: column;
          align-items: flex-start;
        }

        .retailer-price-wrap .retailer-price {
          margin: 4px 0 0;
        }

        .retailer-saving {
          margin-top: 4px;
          color: var(--mint);
          font-size: 12px;
          font-weight: 800;
        }

        .other-matches-button {
          width: calc(100% + 40px);
          margin: 18px -20px -20px;
          min-height: 48px;
          padding: 0 20px;
          border: 0;
          border-top: 1px solid #e2e8f0;
          display: flex;
          align-items: center;
          justify-content: space-between;
          background: #f8fafc;
          color: #334155;
          font: inherit;
          font-size: 12px;
          font-weight: 800;
          cursor: pointer;
        }

        .other-matches-button:hover {
          background: rgba(52, 238, 182, 0.035);
        }

        .retailer-candidate-list {
          margin: 20px -20px -20px;
        }

        .candidate-row {
          grid-template-columns:
            minmax(0, 1.6fr) minmax(110px, 0.45fr) 72px 125px auto;
        }

        .candidate-price {
          font-weight: 800;
          color: #0f172a;
        }


        .search-more-button {
          width: calc(100% - 36px);
          min-height: 42px;
          margin: 14px 18px 16px;
          border-radius: 9px;
          border: 1px solid rgba(52, 238, 182, 0.22);
          background: rgba(52, 238, 182, 0.055);
          color: var(--mint);
          font: inherit;
          font-size: 12px;
          font-weight: 900;
          cursor: pointer;
        }

        .search-more-button:hover {
          background: rgba(52, 238, 182, 0.09);
        }

        .search-more-button:disabled {
          opacity: 0.5;
          cursor: wait;
        }

        .possible-only-panel {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding-top: 10px;
        }

        .possible-only-panel > strong {
          font-size: 18px;
        }

        .possible-only-panel > span {
          color: #64748b;
          font-size: 12px;
        }

        .possible-toggle {
          margin-top: 12px;
        }

        .retailer-no-match {
          display: flex;
          flex-direction: column;
          gap: 6px;
          padding: 14px 0 4px;
        }

        .retailer-no-match span {
          color: #64748b;
          font-size: 12px;
        }

        @media (max-width: 950px) {
          .comparison-summary-card {
            align-items: flex-start;
            flex-direction: column;
          }

          .comparison-summary-metrics {
            width: 100%;
          }

          .retailer-primary-grid {
            grid-template-columns: 1fr;
          }

          .candidate-row {
            grid-template-columns: minmax(0, 1fr) auto auto;
          }

          .candidate-row .match-badge {
            display: none;
          }

          .comparison-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .compare-source-card {
            grid-template-columns: 68px minmax(0, 1fr) repeat(2, minmax(100px, 0.5fr));
          }

          .compare-results-grid {
            grid-template-columns: 1fr;
          }
        }

        @media (max-width: 720px) {
          .comparison-summary-metrics {
            grid-template-columns: 1fr;
            gap: 10px;
          }

          .candidate-row {
            grid-template-columns: minmax(0, 1fr) auto;
          }

          .candidate-score {
            display: none;
          }

          .comparison-header,
          .comparison-shell {
            padding-left: 18px;
            padding-right: 18px;
          }

          .compare-picker {
            grid-template-columns: 1fr;
          }

          .compare-source-card {
            grid-template-columns: 62px minmax(0, 1fr);
          }

          .compare-source-card .compare-metric {
            padding-top: 8px;
          }

          .candidate-row {
            grid-template-columns: minmax(0, 1fr) auto;
          }

          .candidate-row .match-badge {
            display: none;
          }
        }
      `}</style>

      <section className="comparison-dashboard">
          <header className="comparison-header">
            <div>
              <span className="eyebrow">FIND THE BETTER DEAL</span>
              <h2>Price Comparison</h2>
              <p>
                Compare one of your tracked products against other retailers.
              </p>
            </div>
          </header>

          <div className="comparison-shell">
            <section className="glass-card compare-picker">
              <label>
                <span>Product to compare</span>
                <select
                  className="compare-select"
                  value={selectedProductId}
                  onChange={(event) => {
                    const nextId = event.target.value;
                    const nextProduct =
                      products.find((product) => product.id === nextId) ?? null;

                    setSelectedProductId(nextId);
                    setResult(null);
                    setError("");
                    setStoreMenuOpen(false);

                    // V2 can compare alternatives from the tracked retailer too.
                    setSelectedStores(availableCompareStores);
                  }}
                  disabled={loadingProducts || products.length === 0}
                >
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.displayName} · {product.store}
                    </option>
                  ))}
                </select>
              </label>

              <div className="compare-action-wrap">
                <button
                  type="button"
                  className="compare-button"
                  onClick={() => setStoreMenuOpen((current) => !current)}
                  disabled={!selectedProductId || comparing}
                >
                  {comparing ? "Comparing…" : "⌕ Compare Prices ▾"}
                </button>

                {storeMenuOpen && !comparing ? (
                  <div className="store-picker-popover">
                    <div className="store-picker-title">
                      Choose stores to search
                    </div>

                    {availableCompareStores.map((store) => {
                      const isCurrentStore =
                        selectedProduct?.store?.toLowerCase() ===
                        store.toLowerCase();
                      const checked = selectedStores.includes(store);

                      return (
                        <label
                          key={store}
                          className="store-picker-option"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={(event) => {
                              setSelectedStores((current) =>
                                event.target.checked
                                  ? [...current, store]
                                  : current.filter((item) => item !== store),
                              );
                            }}
                          />
                          <span>{store}</span>
                          {isCurrentStore ? (
                            <small>Also searches alternatives here</small>
                          ) : null}
                        </label>
                      );
                    })}

                    <button
                      type="button"
                      className="store-picker-run"
                      disabled={selectedStores.length === 0}
                      onClick={() => {
                        setStoreMenuOpen(false);
                        compareSelectedProduct();
                      }}
                    >
                      Search selected stores
                    </button>
                  </div>
                ) : null}
              </div>
            </section>

            {selectedProduct ? (
              <section className="glass-card compare-source-card">
                <div className="compare-product-image">
                  {selectedProduct.imageUrl ? (
                    <img
                      src={selectedProduct.imageUrl}
                      alt={selectedProduct.displayName}
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <span>◫</span>
                  )}
                </div>

                <div className="compare-product-copy">
                  <span className="compare-label">Currently tracking</span>
                  <strong>{selectedProduct.displayName}</strong>
                  <span>
                    {selectedProduct.store} · {selectedProduct.category}
                  </span>
                </div>

                <div className="compare-metric">
                  <span className="compare-label">Current price</span>
                  <strong>{money(selectedProduct.currentPrice)}</strong>
                </div>

                <div className="compare-metric">
                  <span className="compare-label">Target</span>
                  <strong>{money(selectedProduct.targetPrice)}</strong>
                </div>
              </section>
            ) : null}

            {error ? <div className="comparison-error">{error}</div> : null}

            {!result && !comparing && !error ? (
              <section className="glass-card comparison-empty">
                <div>
                  <strong style={{ display: "block", marginBottom: 7 }}>
                    Choose a product and run a comparison.
                  </strong>
                  <span>
                    Wishlist will search only the retailers you choose, rank possible matches and compare live prices.
                  </span>
                </div>
              </section>
            ) : null}

            {comparing ? (
              <section className="glass-card comparison-empty">
                <div>
                  <strong style={{ display: "block", marginBottom: 7 }}>
                    Searching selected stores…
                  </strong>
                  <span>
                    Matching model numbers, brand and product identity before
                    checking the live price.
                  </span>
                </div>
              </section>
            ) : null}

            {result ? (
              <>
                <section className="glass-card comparison-summary-card">
                  <div>
                    <span className="compare-label">Comparison result</span>
                    <strong>{result.product.comparisonTitle}</strong>
                  </div>

                  <div className="comparison-summary-metrics">
                    <div>
                      <span>Current price</span>
                      <strong>{money(result.product.currentPrice)}</strong>
                    </div>
                    <div>
                      <span>Best found</span>
                      <strong className="mint">
                        {money(overallBestPrice)}
                      </strong>
                    </div>
                    <div>
                      <span>Potential saving</span>
                      <strong className="mint">
                        {sourcePrice !== null &&
                        overallBestPrice !== null &&
                        sourcePrice > overallBestPrice
                          ? money(sourcePrice - overallBestPrice)
                          : "$0.00"}
                      </strong>
                    </div>
                  </div>
                </section>

                <div className="retailer-stack">
                  <article
                    className={`glass-card retailer-card ${
                      overallBestPrice !== null &&
                      sourcePrice === overallBestPrice
                        ? "best"
                        : ""
                    }`}
                  >
                    {overallBestPrice !== null &&
                    sourcePrice === overallBestPrice ? (
                      <span className="best-price-ribbon">Current best</span>
                    ) : null}

                    <div className="retailer-heading">
                      <span className="retailer-mark">
                        {result.product.store?.slice(0, 1) || "W"}
                      </span>
                      <div>
                        <strong>{result.product.store}</strong>
                        <span>Your tracked retailer</span>
                      </div>
                    </div>

                    <div className="retailer-primary-grid">
                      <div>
                        <span className="compare-label">Tracked product</span>
                        <strong className="retailer-product-title">
                          {result.product.comparisonTitle}
                        </strong>
                      </div>

                      <div className="retailer-price-wrap">
                        <span className="compare-label">Current price</span>
                        <div className="retailer-price">
                          {money(result.product.currentPrice)}
                        </div>
                      </div>

                      <Link
                        href={result.product.url}
                        target="_blank"
                        className="store-link"
                      >
                        View current store ↗
                      </Link>
                    </div>
                  </article>

                  {result.retailers.map((retailer) => {
                    const strongest = retailer.strongestMatch;
                    const isBest =
                      strongest?.price !== null &&
                      strongest?.price !== undefined &&
                      strongest.price === overallBestPrice &&
                      sourcePrice !== overallBestPrice;

                    const otherMatches = retailer.matches.slice(1);
                    const isOpen = Boolean(openRetailers[retailer.store]);

                    return (
                      <article
                        key={retailer.store}
                        className={`glass-card retailer-card retailer-comparison-card ${
                          isBest ? "best" : ""
                        }`}
                      >
                        {isBest ? (
                          <span className="best-price-ribbon">Best price</span>
                        ) : null}

                        <div className="retailer-heading">
                          <span className="retailer-mark">
                            {retailer.store.slice(0, 1)}
                          </span>
                          <div>
                            <strong>{retailer.store}</strong>
                            <span>
                              {retailer.searchedCount} candidates searched
                            </span>
                          </div>
                        </div>

                        {retailer.error ? (
                          <div className="comparison-warning">
                            {retailer.error}
                          </div>
                        ) : strongest ? (
                          <>
                            <div className="retailer-primary-grid">
                              <div>
                                <span className="compare-label">
                                  Strongest match
                                </span>
                                <strong className="retailer-product-title">
                                  {strongest.name}
                                </strong>

                                <span
                                  className={`match-badge ${matchClass(
                                    strongest.matchType,
                                  )}`}
                                >
                                  {strongest.matchType} · {strongest.percentage}%
                                </span>
                              </div>

                              <div className="retailer-price-wrap">
                                <span className="compare-label">Live price</span>
                                <div
                                  className={`retailer-price ${
                                    isBest ? "mint" : ""
                                  }`}
                                >
                                  {strongest.price !== null
                                    ? money(strongest.price)
                                    : "Unavailable"}
                                </div>

                                {strongest.saving !== null &&
                                strongest.saving > 0 ? (
                                  <span className="retailer-saving">
                                    Save {money(strongest.saving)}
                                  </span>
                                ) : null}
                              </div>

                              <Link
                                href={strongest.url}
                                target="_blank"
                                className="store-link"
                              >
                                View store ↗
                              </Link>
                            </div>

                            {strongest.priceError ? (
                              <div className="comparison-warning">
                                Live price temporarily unavailable.
                              </div>
                            ) : null}

                            {otherMatches.length > 0 || retailer.hasMore ? (
                              <>
                                <button
                                  type="button"
                                  className="other-matches-button"
                                  onClick={() =>
                                    setOpenRetailers((current) => ({
                                      ...current,
                                      [retailer.store]:
                                        !current[retailer.store],
                                    }))
                                  }
                                >
                                  <span>
                                    {isOpen ? "Hide" : "Show"} other{" "}
                                    {retailer.store} matches
                                  </span>
                                  <span>{isOpen ? "⌃" : "⌄"}</span>
                                </button>

                                {isOpen ? (
                                  <div className="candidate-list retailer-candidate-list">
                                    {otherMatches.map((candidate, index) => (
                                      <div
                                        className="candidate-row"
                                        key={`${candidate.url}-${index}`}
                                      >
                                        <div className="candidate-copy">
                                          <strong>{candidate.name}</strong>
                                          <span>
                                            {candidate.reasons?.length
                                              ? candidate.reasons.join(" · ")
                                              : `${candidate.percentage}% match confidence`}
                                          </span>
                                        </div>

                                        <span className="candidate-price">
                                          {candidate.price !== null
                                            ? money(candidate.price)
                                            : "Price unavailable"}
                                        </span>

                                        <span className="candidate-score">
                                          {candidate.percentage}%
                                        </span>

                                        <span
                                          className={`match-badge ${matchClass(
                                            candidate.matchType,
                                          )}`}
                                        >
                                          {candidate.matchType}
                                        </span>

                                        <Link
                                          href={candidate.url}
                                          target="_blank"
                                          className="store-link"
                                          style={{ marginTop: 0 }}
                                        >
                                          Open ↗
                                        </Link>
                                      </div>
                                    ))}

                                    {retailer.hasMore ? (
                                      <button
                                        type="button"
                                        className="search-more-button"
                                        disabled={Boolean(
                                          loadingMoreStores[retailer.store],
                                        )}
                                        onClick={() =>
                                          loadMoreMatches(
                                            retailer.store,
                                            retailer.nextOffset,
                                          )
                                        }
                                      >
                                        {loadingMoreStores[retailer.store]
                                          ? "Searching for more…"
                                          : "Search for 5 more matches"}
                                      </button>
                                    ) : null}
                                  </div>
                                ) : null}
                              </>
                            ) : null}
                          </>
                        ) : retailer.reason === "POSSIBLE_ONLY" ? (
                          <div className="possible-only-panel">
                            <strong>No confident match</strong>
                            <span>
                              Wishlist found possible matches, but none were
                              strong enough to promote as the main retailer result.
                            </span>

                            {retailer.matches.length > 0 ? (
                              <>
                                <button
                                  type="button"
                                  className="other-matches-button possible-toggle"
                                  onClick={() =>
                                    setOpenRetailers((current) => ({
                                      ...current,
                                      [retailer.store]:
                                        !current[retailer.store],
                                    }))
                                  }
                                >
                                  <span>
                                    {isOpen ? "Hide" : "Show"} possible{" "}
                                    {retailer.store} matches
                                  </span>
                                  <span>{isOpen ? "⌃" : "⌄"}</span>
                                </button>

                                {isOpen ? (
                                  <div className="candidate-list retailer-candidate-list">
                                    {retailer.matches.map((candidate, index) => (
                                      <div
                                        className="candidate-row"
                                        key={`${candidate.url}-${index}`}
                                      >
                                        <div className="candidate-copy">
                                          <strong>{candidate.name}</strong>
                                          <span>
                                            {candidate.reasons?.length
                                              ? candidate.reasons.join(" · ")
                                              : `${candidate.percentage}% match confidence`}
                                          </span>
                                        </div>

                                        <span className="candidate-price">
                                          {candidate.price !== null
                                            ? money(candidate.price)
                                            : "Price unavailable"}
                                        </span>

                                        <span className="candidate-score">
                                          {candidate.percentage}%
                                        </span>

                                        <span
                                          className={`match-badge ${matchClass(
                                            candidate.matchType,
                                          )}`}
                                        >
                                          {candidate.matchType}
                                        </span>

                                        <Link
                                          href={candidate.url}
                                          target="_blank"
                                          className="store-link"
                                          style={{ marginTop: 0 }}
                                        >
                                          Open ↗
                                        </Link>
                                      </div>
                                    ))}

                                    {retailer.hasMore ? (
                                      <button
                                        type="button"
                                        className="search-more-button"
                                        disabled={Boolean(
                                          loadingMoreStores[retailer.store],
                                        )}
                                        onClick={() =>
                                          loadMoreMatches(
                                            retailer.store,
                                            retailer.nextOffset,
                                          )
                                        }
                                      >
                                        {loadingMoreStores[retailer.store]
                                          ? "Searching for more…"
                                          : "Search for 5 more matches"}
                                      </button>
                                    ) : null}
                                  </div>
                                ) : null}
                              </>
                            ) : null}
                          </div>
                        ) : (
                          <div className="retailer-no-match">
                            <strong>No matches found</strong>
                            <span>
                              Wishlist searched {retailer.searchedCount}{" "}
                              results, but none were close enough to show.
                            </span>
                          </div>
                        )}
                      </article>
                    );
                  })}
                </div>
              </>
            ) : null}
          </div>
        </section>
    </>
  );
}
