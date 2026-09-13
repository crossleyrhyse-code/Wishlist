"use client";

import { useEffect, useMemo, useState } from "react";
import { loadWishlistProducts } from "../data/wishlistProducts";
import Sidebar from "../components/Sidebar";


type PriceHistoryEntry = {
  checkedAt: string;
  price: number;
};

type WishlistProduct = {
  id: string;
  displayName: string;
  store: string;
  imageUrl: string | null;
  currentPrice: number | null;
  addedPrice: number | null;
  lastChecked: string | null;
  priceHistory: PriceHistoryEntry[];
};

function money(value: number | null) {
  if (value === null) return "—";

  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

function compactMoney(value: number) {
  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
    maximumFractionDigits: 0,
  }).format(value);
}

function shortDate(value: string) {
  return new Intl.DateTimeFormat("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  }).format(new Date(value));
}

export default function PriceHistoryPage() {
  const [products, setProducts] = useState<WishlistProduct[]>([]);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [range, setRange] = useState("6");
  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    async function loadProducts() {
      try {
        const data = (await loadWishlistProducts()) as WishlistProduct[];
        setProducts(data);

        if (data.length > 0) {
          setSelectedProductId(data[0].id);
        } else {
          setSelectedProductId("");
        }

        setLoadError("");
      } catch (error) {
        setProducts([]);
        setSelectedProductId("");
        setLoadError(
          error instanceof Error
            ? error.message
            : "Could not load Wishlist products.",
        );
      }
    }

    loadProducts();
  }, []);

  const selectedProduct = useMemo(
    () =>
      products.find((product) => product.id === selectedProductId) ??
      products[0] ??
      null,
    [products, selectedProductId],
  );

  const history = useMemo(() => {
    if (!selectedProduct) return [];

    const months = range === "all" ? null : Number(range);

    const cutoff =
      months === null
        ? null
        : new Date(
            new Date().setMonth(new Date().getMonth() - months),
          ).getTime();

    let points = [...(selectedProduct.priceHistory ?? [])]
      .filter(
        (entry) =>
          Number.isFinite(entry.price) &&
          Number.isFinite(new Date(entry.checkedAt).getTime()),
      )
      .sort(
        (a, b) =>
          new Date(a.checkedAt).getTime() -
          new Date(b.checkedAt).getTime(),
      );

    if (cutoff !== null) {
      points = points.filter(
        (entry) => new Date(entry.checkedAt).getTime() >= cutoff,
      );
    }

    if (selectedProduct.currentPrice !== null) {
      const latest = points[points.length - 1];

      if (
        !latest ||
        latest.price !== selectedProduct.currentPrice ||
        (selectedProduct.lastChecked &&
          latest.checkedAt !== selectedProduct.lastChecked)
      ) {
        points.push({
          checkedAt:
            selectedProduct.lastChecked ?? new Date().toISOString(),
          price: selectedProduct.currentPrice,
        });
      }
    }

    return points;
  }, [selectedProduct, range]);

  const stats = useMemo(() => {
    if (!history.length) {
      return {
        lowest: null,
        highest: null,
        average: null,
        change: null,
      };
    }

    const lowest = history.reduce((best, entry) =>
      entry.price < best.price ? entry : best,
    );

    const highest = history.reduce((best, entry) =>
      entry.price > best.price ? entry : best,
    );

    const average =
      history.reduce((total, entry) => total + entry.price, 0) /
      history.length;

    const change =
      history[history.length - 1].price - history[0].price;

    return {
      lowest,
      highest,
      average,
      change,
    };
  }, [history]);

  const chart = useMemo(() => {
    if (!history.length) {
      return {
        points: [] as {
          x: number;
          y: number;
          entry: PriceHistoryEntry;
        }[],
        line: "",
        area: "",
        ticks: [] as number[],
      };
    }

    const width = 1000;
    const height = 390;

    const left = 70;
    const right = 25;
    const top = 25;
    const bottom = 50;

    const chartWidth = width - left - right;
    const chartHeight = height - top - bottom;

    const rawMin = Math.min(...history.map((entry) => entry.price));
    const rawMax = Math.max(...history.map((entry) => entry.price));

    const spread = Math.max(
      rawMax - rawMin,
      Math.max(rawMax * 0.08, 10),
    );

    const padding = spread * 0.2;

    const minPrice = Math.max(0, rawMin - padding);
    const maxPrice = rawMax + padding;

    const points = history.map((entry, index) => {
      const x =
        history.length === 1
          ? left + chartWidth / 2
          : left + (index / (history.length - 1)) * chartWidth;

      const y =
        top +
        ((maxPrice - entry.price) /
          Math.max(maxPrice - minPrice, 1)) *
          chartHeight;

      return {
        x,
        y,
        entry,
      };
    });

    const line = points
      .map(
        (point, index) =>
          `${index === 0 ? "M" : "L"} ${point.x} ${point.y}`,
      )
      .join(" ");

    const area =
      points.length > 1
        ? `${line} L ${points[points.length - 1].x} ${
            top + chartHeight
          } L ${points[0].x} ${top + chartHeight} Z`
        : "";

    const ticks = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4;
      return maxPrice - (maxPrice - minPrice) * ratio;
    });

    return {
      points,
      line,
      area,
      ticks,
    };
  }, [history]);

  return (
    <>
      <style jsx global>{`
        .history-page {
          padding-bottom: 40px;
        }

        .history-header {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 24px;
        }

        .history-header h2 {
          margin: 4px 0 5px;
          font-size: 30px;
        }

        .history-header p {
          margin: 0;
          color: rgba(235, 243, 242, 0.55);
        }

        .history-controls {
          display: flex;
          gap: 10px;
          align-items: center;
        }

        .history-select {
          min-width: 200px;
          height: 42px;
          padding: 0 36px 0 13px;
          border-radius: 11px;
          border: 1px solid rgba(255, 255, 255, 0.09);
          background: rgba(5, 15, 17, 0.82);
          color: rgba(246, 250, 249, 0.95);
          font: inherit;
          font-size: 12px;
          font-weight: 700;
          outline: none;
        }

        .history-select.range {
          min-width: 145px;
        }

        .history-chart-card {
          padding: 0;
          overflow: hidden;
        }

        .history-card-header {
          display: flex;
          justify-content: space-between;
          gap: 20px;
          align-items: center;
          padding: 20px 22px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .history-product-heading {
          display: flex;
          align-items: center;
          gap: 14px;
          min-width: 0;
        }

        .history-product-image {
          width: 48px;
          height: 48px;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.08);
          background: rgba(255, 255, 255, 0.04);
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          flex: 0 0 auto;
        }

        .history-product-image img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .history-product-heading h3 {
          margin: 0 0 3px;
          font-size: 17px;
        }

        .history-product-heading span {
          color: rgba(235, 243, 242, 0.5);
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 0.06em;
        }

        .history-current {
          text-align: right;
        }

        .history-current span {
          display: block;
          color: rgba(235, 243, 242, 0.48);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.08em;
        }

        .history-current strong {
          display: block;
          margin-top: 3px;
          color: var(--mint);
          font-size: 24px;
        }

        .history-chart-wrap {
          padding: 20px 24px 10px;
        }

        .history-chart-surface {
          padding: 14px;
          border-radius: 14px;
          background: rgba(3, 13, 15, 0.33);
          border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .history-chart {
          width: 100%;
          height: 390px;
          display: block;
          overflow: visible;
        }

        .history-grid {
          stroke: rgba(175, 205, 202, 0.12);
          stroke-width: 1;
        }

        .history-axis-label {
          fill: rgba(225, 237, 235, 0.58);
          font-size: 11px;
          font-weight: 600;
        }

        .history-area {
          fill: rgba(52, 238, 182, 0.1);
        }

        .history-line {
          fill: none;
          stroke: var(--mint);
          stroke-width: 3;
          stroke-linecap: round;
          stroke-linejoin: round;
        }

        .history-point {
          fill: var(--mint);
          stroke: rgba(4, 18, 19, 0.94);
          stroke-width: 2;
        }

        .history-stats {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 12px;
          padding: 10px 24px 24px;
        }

        .history-stat {
          padding: 15px;
          border-radius: 12px;
          background: rgba(5, 15, 17, 0.5);
          border: 1px solid rgba(255, 255, 255, 0.06);
        }

        .history-stat span {
          display: block;
          margin-bottom: 5px;
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.07em;
          color: rgba(235, 243, 242, 0.48);
          text-transform: uppercase;
        }

        .history-stat strong {
          font-size: 17px;
        }

        .history-empty {
          min-height: 390px;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: rgba(235, 243, 242, 0.5);
          gap: 8px;
        }

        .history-empty strong {
          color: rgba(245, 249, 248, 0.9);
          font-size: 17px;
        }

        @media (max-width: 1050px) {
          .history-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .history-controls {
            width: 100%;
          }

          .history-select {
            flex: 1;
          }

          .history-stats {
            grid-template-columns: repeat(2, 1fr);
          }
        }

        @media (max-width: 700px) {
          .history-controls {
            flex-direction: column;
          }

          .history-select {
            width: 100%;
          }

          .history-stats {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <main className="site-shell">
        <div className="background-layer" aria-hidden="true" />
        <div className="background-shade" aria-hidden="true" />

        <Sidebar />

        <section className="dashboard history-page">
          <header className="history-header">
            <div>
              <span className="eyebrow">PRICE TRACKING</span>
              <h2>Price History</h2>
              <p>See how your tracked products have changed over time.</p>
            </div>

            <div className="history-controls">
              <select
                className="history-select"
                value={selectedProduct?.id ?? ""}
                onChange={(event) =>
                  setSelectedProductId(event.target.value)
                }
              >
                {products.map((product) => (
                  <option key={product.id} value={product.id}>
                    {product.displayName}
                  </option>
                ))}
              </select>

              <select
                className="history-select range"
                value={range}
                onChange={(event) => setRange(event.target.value)}
              >
                <option value="1">Last month</option>
                <option value="3">Last 3 months</option>
                <option value="6">Last 6 months</option>
                <option value="12">Last 12 months</option>
                <option value="all">All history</option>
              </select>
            </div>
          </header>

          {loadError ? (
            <section className="glass-card history-empty">
              <strong>Could not load price history.</strong>
              <span>{loadError}</span>
            </section>
          ) : !selectedProduct ? (
            <section className="glass-card history-empty">
              <strong>No products yet</strong>
              <span>Add a product to start building price history.</span>
            </section>
          ) : (
            <section className="glass-card history-chart-card">
              <div className="history-card-header">
                <div className="history-product-heading">
                  <div className="history-product-image">
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

                  <div>
                    <h3>{selectedProduct.displayName}</h3>
                    <span>{selectedProduct.store}</span>
                  </div>
                </div>

                <div className="history-current">
                  <span>CURRENT PRICE</span>
                  <strong>
                    {money(selectedProduct.currentPrice)}
                  </strong>
                </div>
              </div>

              {!history.length ? (
                <div className="history-empty">
                  <strong>No price history yet</strong>
                  <span>
                    Wishlist will build this chart as prices are checked.
                  </span>
                </div>
              ) : (
                <>
                  <div className="history-chart-wrap">
                    <div className="history-chart-surface">
                      <svg
                        className="history-chart"
                        viewBox="0 0 1000 390"
                        role="img"
                        aria-label={`Price history for ${selectedProduct.displayName}`}
                      >
                        {chart.ticks.map((tick, index) => {
                          const top = 25;
                          const bottom = 50;
                          const chartHeight = 390 - top - bottom;

                          const y =
                            top +
                            (index /
                              Math.max(chart.ticks.length - 1, 1)) *
                              chartHeight;

                          return (
                            <g key={`${tick}-${index}`}>
                              <line
                                className="history-grid"
                                x1="70"
                                x2="975"
                                y1={y}
                                y2={y}
                              />

                              <text
                                className="history-axis-label"
                                x="60"
                                y={y + 4}
                                textAnchor="end"
                              >
                                {compactMoney(tick)}
                              </text>
                            </g>
                          );
                        })}

                        {chart.area && (
                          <path
                            className="history-area"
                            d={chart.area}
                          />
                        )}

                        <path
                          className="history-line"
                          d={chart.line}
                        />

                        {chart.points.map((point, index) => (
                          <g key={`${point.entry.checkedAt}-${index}`}>
                            <circle
                              className="history-point"
                              cx={point.x}
                              cy={point.y}
                              r="5"
                            >
                              <title>
                                {shortDate(point.entry.checkedAt)} —{" "}
                                {money(point.entry.price)}
                              </title>
                            </circle>

                            {(index === 0 ||
                              index === chart.points.length - 1) && (
                              <text
                                className="history-axis-label"
                                x={point.x}
                                y="375"
                                textAnchor={
                                  index === 0 ? "start" : "end"
                                }
                              >
                                {shortDate(point.entry.checkedAt)}
                              </text>
                            )}
                          </g>
                        ))}
                      </svg>
                    </div>
                  </div>

                  <div className="history-stats">
                    <div className="history-stat">
                      <span>Lowest Price</span>
                      <strong>
                        {stats.lowest
                          ? money(stats.lowest.price)
                          : "—"}
                      </strong>
                    </div>

                    <div className="history-stat">
                      <span>Highest Price</span>
                      <strong>
                        {stats.highest
                          ? money(stats.highest.price)
                          : "—"}
                      </strong>
                    </div>

                    <div className="history-stat">
                      <span>Average Price</span>
                      <strong>{money(stats.average)}</strong>
                    </div>

                    <div className="history-stat">
                      <span>Price Change</span>
                      <strong>
                        {stats.change === null
                          ? "—"
                          : `${stats.change > 0 ? "+" : ""}${money(
                              stats.change,
                            )}`}
                      </strong>
                    </div>
                  </div>
                </>
              )}
            </section>
          )}
        </section>
      </main>
    </>
  );
}