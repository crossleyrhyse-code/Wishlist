"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { loadWishlistProducts } from "./data/wishlistProducts";
type PriceHistoryEntry = {
  checkedAt: string;
  price: number;
};

type AlertMode =
  | "TARGET_REACHED"
  | "PRICE_DROP"
  | "PRICE_CHANGE"
  | "DAILY_DIGEST"
  | "WEEKLY_DIGEST"
  | "OFF";

type AlertSettings = {
  mode: AlertMode;
  emailEnabled: boolean;
};

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
  addedPrice: number | null;
  priceSelector: string | null;
  source: string;
  addedOrder: number;
  lastChecked: string | null;
  priceHistory: PriceHistoryEntry[];
  alertSettings?: AlertSettings;
};

function money(value: number | null) {
  if (value === null) return "Not checked";

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

function monthLabel(value: string) {
  return new Intl.DateTimeFormat("en-AU", {
    month: "short",
  }).format(new Date(value));
}

function alertLabel(mode?: AlertMode) {
  switch (mode) {
    case "TARGET_REACHED":
      return "Target";
    case "PRICE_DROP":
      return "Price drop";
    case "PRICE_CHANGE":
      return "Price change";
    case "DAILY_DIGEST":
      return "Daily";
    case "WEEKLY_DIGEST":
      return "Weekly";
    case "OFF":
      return "Off";
    default:
      return "Target";
  }
}

function toTarget(product: WishlistProduct) {
  if (product.currentPrice === null || product.targetPrice === null) {
    return null;
  }

  return product.currentPrice - product.targetPrice;
}


function getPreviousRecordedPrice(product: WishlistProduct) {
  if (product.currentPrice === null) {
    return null;
  }

  const history = [...(product.priceHistory ?? [])]
    .filter((entry) => Number.isFinite(entry.price))
    .sort(
      (a, b) =>
        new Date(a.checkedAt).getTime() - new Date(b.checkedAt).getTime(),
    );

  for (let index = history.length - 1; index >= 0; index -= 1) {
    const recordedPrice = history[index].price;

    if (recordedPrice !== product.currentPrice) {
      return recordedPrice;
    }
  }

  if (
    product.addedPrice !== null &&
    product.addedPrice !== product.currentPrice
  ) {
    return product.addedPrice;
  }

  return null;
}

function getPriceDropAmount(product: WishlistProduct) {
  const previousPrice = getPreviousRecordedPrice(product);

  if (previousPrice === null || product.currentPrice === null) {
    return 0;
  }

  return Math.max(previousPrice - product.currentPrice, 0);
}

function Sparkline() {
  return (
    <svg className="sparkline" viewBox="0 0 240 34" aria-hidden="true">
      <path d="M2 22 C20 10, 35 28, 54 18 S88 26, 106 17 S138 25, 158 16 S194 22, 238 10" />
    </svg>
  );
}

function StatCard({
  icon,
  title,
  value,
  subtitle,
  tone = "mint",
  href = "/products",
  details = [],
}: {
  icon: string;
  title: string;
  value: string;
  subtitle: string;
  tone?: "mint" | "amber" | "blue";
  href?: string;
  details?: { label: string; value: string; accent?: boolean }[];
}) {
  return (
    <article className="glass-card stat-card dashboard-stat-card">
      <div className="stat-card-top">
        <div className={`icon-circle ${tone}`}>{icon}</div>

        <div className="stat-copy">
          <span className="eyebrow">{title}</span>
          <strong className="stat-value">{value}</strong>
        </div>

        <Link href={href} className="icon-button" aria-label={`Open ${title}`}>
          ›
        </Link>
      </div>

      <div className="stat-detail-list">
        {details.slice(0, 3).map((detail) => (
          <div className="stat-detail-row" key={`${detail.label}-${detail.value}`}>
            <span className="stat-detail-dot" />
            <span className="stat-detail-label">{detail.label}</span>
            <strong className={detail.accent ? "stat-detail-value accent" : "stat-detail-value"}>
              {detail.value}
            </strong>
          </div>
        ))}
      </div>

      <Link href={href} className="stat-card-bottom stat-card-link">
        <span>{subtitle}</span>
        <span className="chevron">›</span>
      </Link>
    </article>
  );
}

function ProductThumb({ product }: { product: WishlistProduct }) {
  if (product.imageUrl) {
    return (
      <div className="product-thumb">
        <img
          src={product.imageUrl}
          alt={product.displayName}
          loading="lazy"
          referrerPolicy="no-referrer"
          style={{
            width: "100%",
            height: "100%",
            objectFit: "contain",
            borderRadius: "inherit",
          }}
        />
      </div>
    );
  }

  return <div className="product-thumb">◫</div>;
}

export default function Home() {
  const [products, setProducts] = useState<WishlistProduct[]>([]);
  const [loadError, setLoadError] = useState("");
  const [sort, setSort] = useState("recent");
  const [trendProductId, setTrendProductId] = useState("");
  const [trendRange, setTrendRange] = useState("6");

  useEffect(() => {
    async function loadProducts() {
      try {
        const result = (await loadWishlistProducts()) as WishlistProduct[];
        setProducts(result);
        setLoadError("");
      } catch (error) {
        setProducts([]);
        setLoadError(
          error instanceof Error
            ? error.message
            : "Could not load Wishlist products.",
        );
      }
    }

    loadProducts();
  }, []);

  useEffect(() => {
    if (!products.length) {
      setTrendProductId("");
      return;
    }

    const stillExists = products.some((product) => product.id === trendProductId);

    if (!trendProductId || !stillExists) {
      setTrendProductId(products[0].id);
    }
  }, [products, trendProductId]);

  const trackedCount = products.length;

  const priceDropProducts = useMemo(
    () => products.filter((product) => getPriceDropAmount(product) > 0),
    [products],
  );

  const biggestPriceDrop = useMemo(() => {
    let bestProduct: WishlistProduct | null = null;
    let bestDrop = 0;

    for (const product of products) {
      const drop = getPriceDropAmount(product);

      if (drop > bestDrop) {
        bestDrop = drop;
        bestProduct = product;
      }
    }

    return {
      product: bestProduct,
      drop: bestDrop,
    };
  }, [products]);

  const activeAlertCount = useMemo(
    () =>
      products.filter(
        (product) =>
          (product.alertSettings?.mode ?? "TARGET_REACHED") !== "OFF",
      ).length,
    [products],
  );

  const alertBreakdown = useMemo(() => {
    const active = products.filter(
      (product) => (product.alertSettings?.mode ?? "TARGET_REACHED") !== "OFF",
    );

    return {
      target: active.filter(
        (product) => (product.alertSettings?.mode ?? "TARGET_REACHED") === "TARGET_REACHED",
      ).length,
      drops: active.filter((product) => product.alertSettings?.mode === "PRICE_DROP").length,
      digest: active.filter((product) =>
        ["DAILY_DIGEST", "WEEKLY_DIGEST"].includes(product.alertSettings?.mode ?? ""),
      ).length,
    };
  }, [products]);

  const trackedBreakdown = useMemo(() => {
    const checked = products.filter((product) => product.currentPrice !== null).length;
    const withTargets = products.filter((product) => product.targetPrice !== null).length;
    const stores = new Set(products.map((product) => product.store).filter(Boolean)).size;
    return { checked, withTargets, stores };
  }, [products]);

  const hottestProduct = useMemo(() => {
    // PRICE-DROP MODE:
    // As soon as we have a real recorded price drop, the hottest product
    // becomes the product with the biggest recorded drop. It stays that way
    // until another product records an even bigger drop.
    let biggestDropProduct: WishlistProduct | null = null;
    let biggestDrop = 0;

    for (const product of products) {
      const drop = getPriceDropAmount(product);

      if (drop > biggestDrop) {
        biggestDrop = drop;
        biggestDropProduct = product;
      }
    }

    if (biggestDropProduct) {
      return {
        product: biggestDropProduct,
        saving: biggestDrop,
        source: "PRICE_DROP" as const,
      };
    }

    // TARGET-SAVING MODE:
    // Until a genuine price drop exists, use the product that is furthest
    // below its target price.
    let bestTargetProduct: WishlistProduct | null = null;
    let bestTargetSaving = 0;

    for (const product of products) {
      if (product.currentPrice === null || product.targetPrice === null) {
        continue;
      }

      const targetSaving = product.targetPrice - product.currentPrice;

      if (targetSaving > bestTargetSaving) {
        bestTargetSaving = targetSaving;
        bestTargetProduct = product;
      }
    }

    return {
      product: bestTargetProduct,
      saving: bestTargetSaving,
      source: "TARGET_SAVING" as const,
    };
  }, [products]);

  const recentProducts = useMemo(() => {
    return [...products]
      .sort((a, b) => {
        if (sort === "cheapest") {
          if (a.currentPrice === null && b.currentPrice === null) return 0;
          if (a.currentPrice === null) return 1;
          if (b.currentPrice === null) return -1;
          return a.currentPrice - b.currentPrice;
        }

        if (sort === "savings") {
          const aSaving =
            a.currentPrice !== null && a.addedPrice !== null
              ? a.addedPrice - a.currentPrice
              : Number.NEGATIVE_INFINITY;

          const bSaving =
            b.currentPrice !== null && b.addedPrice !== null
              ? b.addedPrice - b.currentPrice
              : Number.NEGATIVE_INFINITY;

          return bSaving - aSaving;
        }

        if (sort === "name") {
          return a.displayName.localeCompare(b.displayName);
        }

        return b.addedOrder - a.addedOrder;
      });
  }, [products, sort]);

  const trendProduct = useMemo(
    () =>
      products.find((product) => product.id === trendProductId) ??
      products[0] ??
      null,
    [products, trendProductId],
  );

  const trendData = useMemo(() => {
    if (!trendProduct) {
      return {
        points: [] as PriceHistoryEntry[],
        average: null as number | null,
        lowest: null as PriceHistoryEntry | null,
        highest: null as PriceHistoryEntry | null,
        totalChange: null as number | null,
        percentChange: null as number | null,
      };
    }

    const now = Date.now();
    const months = trendRange === "all" ? null : Number(trendRange);
    const cutoff =
      months === null
        ? null
        : new Date(new Date(now).setMonth(new Date(now).getMonth() - months)).getTime();

    let points = [...(trendProduct.priceHistory ?? [])]
      .filter(
        (entry) =>
          Number.isFinite(entry.price) &&
          Number.isFinite(new Date(entry.checkedAt).getTime()),
      )
      .sort(
        (a, b) =>
          new Date(a.checkedAt).getTime() - new Date(b.checkedAt).getTime(),
      );

    if (cutoff !== null) {
      points = points.filter(
        (entry) => new Date(entry.checkedAt).getTime() >= cutoff,
      );
    }

    // Make sure the latest known price is represented even if history is sparse.
    if (trendProduct.currentPrice !== null) {
      const latestHistoryPrice = points.at(-1)?.price ?? null;
      const latestHistoryTime = points.at(-1)?.checkedAt ?? null;

      if (
        latestHistoryPrice !== trendProduct.currentPrice ||
        (trendProduct.lastChecked &&
          latestHistoryTime !== trendProduct.lastChecked)
      ) {
        points.push({
          checkedAt:
            trendProduct.lastChecked ?? new Date().toISOString(),
          price: trendProduct.currentPrice,
        });
      }
    }

    if (!points.length) {
      return {
        points,
        average: null,
        lowest: null,
        highest: null,
        totalChange: null,
        percentChange: null,
      };
    }

    const average =
      points.reduce((total, point) => total + point.price, 0) / points.length;

    const lowest = points.reduce((best, point) =>
      point.price < best.price ? point : best,
    );

    const highest = points.reduce((best, point) =>
      point.price > best.price ? point : best,
    );

    const first = points[0].price;
    const last = points[points.length - 1].price;
    const totalChange = last - first;
    const percentChange = first ? (totalChange / first) * 100 : null;

    return {
      points,
      average,
      lowest,
      highest,
      totalChange,
      percentChange,
    };
  }, [trendProduct, trendRange]);

  const chartGeometry = useMemo(() => {
    const points = trendData.points;

    if (!points.length) {
      return {
        plotted: [] as { x: number; y: number; point: PriceHistoryEntry }[],
        line: "",
        area: "",
        minPrice: 0,
        maxPrice: 0,
        yTicks: [] as number[],
      };
    }

    const width = 820;
    const height = 300;
    const left = 62;
    const right = 18;
    const top = 18;
    const bottom = 42;
    const innerWidth = width - left - right;
    const innerHeight = height - top - bottom;

    const rawMin = Math.min(...points.map((point) => point.price));
    const rawMax = Math.max(...points.map((point) => point.price));
    const spread = Math.max(rawMax - rawMin, Math.max(rawMax * 0.08, 10));
    const pad = spread * 0.22;
    const minPrice = Math.max(0, rawMin - pad);
    const maxPrice = rawMax + pad;

    const plotted = points.map((point, index) => {
      const x =
        points.length === 1
          ? left + innerWidth / 2
          : left + (index / (points.length - 1)) * innerWidth;

      const y =
        top +
        ((maxPrice - point.price) / Math.max(maxPrice - minPrice, 1)) *
          innerHeight;

      return { x, y, point };
    });

    const line = plotted
      .map((entry, index) => `${index === 0 ? "M" : "L"} ${entry.x} ${entry.y}`)
      .join(" ");

    const area =
      plotted.length > 1
        ? `${line} L ${plotted[plotted.length - 1].x} ${top + innerHeight} L ${
            plotted[0].x
          } ${top + innerHeight} Z`
        : "";

    const yTicks = Array.from({ length: 5 }, (_, index) => {
      const ratio = index / 4;
      return maxPrice - (maxPrice - minPrice) * ratio;
    });

    return { plotted, line, area, minPrice, maxPrice, yTicks };
  }, [trendData.points]);

  return (
    <>
      <style jsx global>{`
        .dashboard-stat-grid {
          align-items: stretch;
        }

        .dashboard-header .notification-button {
          position: relative;
          width: 44px;
          height: 44px;
          min-width: 44px;
          padding: 0;
          border-radius: 12px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: rgba(21, 29, 31, 0.68);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: rgba(248, 251, 250, 0.92);
          text-decoration: none;
          line-height: 1;
          overflow: visible;
        }

        .dashboard-header .notification-button:hover {
          background: rgba(27, 38, 40, 0.88);
          border-color: rgba(52, 238, 182, 0.28);
        }

        .dashboard-header .notification-bell {
          width: 19px;
          height: 19px;
          display: block;
          flex: 0 0 auto;
        }

        .dashboard-header .notification-badge {
          position: absolute;
          top: -6px;
          right: -6px;
          min-width: 19px;
          height: 19px;
          padding: 0 5px;
          border-radius: 999px;
          display: inline-flex;
          align-items: center;
          justify-content: center;
          background: #ff4964;
          border: 2px solid rgba(13, 20, 22, 0.96);
          color: white;
          font-size: 10px;
          font-weight: 800;
          line-height: 1;
          box-sizing: border-box;
          z-index: 2;
        }

        .dashboard-stat-card {
          height: 238px;
          min-height: 238px;
          display: flex;
          flex-direction: column;
          overflow: hidden;
        }

        .dashboard-stat-card .stat-card-top {
          flex: 0 0 auto;
        }

        .stat-detail-list {
          display: flex;
          flex-direction: column;
          gap: 7px;
          margin: 14px 0 10px;
          min-height: 72px;
        }

        .stat-detail-row {
          display: grid;
          grid-template-columns: 8px minmax(0, 1fr) auto;
          align-items: center;
          gap: 8px;
          min-width: 0;
          font-size: 11px;
        }

        .stat-detail-dot {
          width: 5px;
          height: 5px;
          border-radius: 999px;
          background: var(--mint);
          box-shadow: 0 0 8px rgba(52, 238, 182, 0.45);
        }

        .stat-detail-label {
          color: rgba(239, 246, 245, 0.58);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .stat-detail-value {
          max-width: 120px;
          color: rgba(245, 249, 248, 0.92);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          text-align: right;
        }

        .stat-detail-value.accent {
          color: var(--mint);
        }

        .stat-card-link {
          margin-top: auto;
          text-decoration: none;
          color: inherit;
        }

        .dashboard-stat-card .sparkline {
          display: none;
        }

        @media (max-width: 1450px) {
          .dashboard-stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
          }

          .dashboard-stat-card {
            height: 220px;
            min-height: 220px;
          }

          .stat-detail-value {
            max-width: 180px;
          }
        }

        @media (max-width: 820px) {
          .dashboard-stat-grid {
            grid-template-columns: 1fr !important;
          }

          .dashboard-stat-card {
            height: auto;
            min-height: 210px;
          }
        }


        .recent-products-layout {
          grid-template-columns: 1fr !important;
        }

        .recent-metric {
          display: flex;
          flex-direction: column;
          gap: 3px;
          min-width: 0;
        }

        .recent-metric-label {
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.08em;
          text-transform: uppercase;
          color: rgba(235, 243, 242, 0.46);
        }

        .recent-alert-status {
          display: inline-flex;
          align-items: center;
          gap: 8px;
          font-size: 12px;
          font-weight: 700;
          color: rgba(239, 246, 245, 0.82);
          white-space: nowrap;
        }

        .recent-alert-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          flex: 0 0 auto;
        }

        .recent-row-tail {
          display: flex;
          align-items: center;
          justify-content: flex-end;
          gap: 10px;
          min-width: 44px;
        }

        .recent-products-panel .drop-row {
          min-height: 72px;
        }

        @media (max-width: 1320px) {
          .recent-products-panel .drop-row {
            grid-template-columns:
              54px minmax(210px, 1.55fr) minmax(86px, 0.7fr)
              minmax(86px, 0.7fr) minmax(92px, 0.75fr) auto !important;
          }

          .recent-alert-status {
            display: none;
          }
        }

        @media (max-width: 1120px) {
          .recent-products-panel .drop-row {
            grid-template-columns:
              54px minmax(190px, 1.6fr) minmax(86px, 0.75fr)
              minmax(90px, 0.8fr) auto !important;
          }

          .recent-products-panel .drop-row .recent-metric:nth-of-type(2) {
            display: none;
          }
        }


        .price-trend-panel {
          overflow: hidden;
        }

        .price-trend-panel .panel-header {
          gap: 14px;
        }

        .trend-controls {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-left: auto;
        }

        .trend-select {
          min-width: 190px;
          height: 38px;
          padding: 0 34px 0 12px;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.09);
          background: rgba(5, 15, 17, 0.78);
          color: rgba(246, 250, 249, 0.94);
          font: inherit;
          font-size: 12px;
          font-weight: 700;
          outline: none;
        }

        .trend-select.range {
          min-width: 124px;
        }

        .trend-chart-layout {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 190px;
          gap: 18px;
          padding: 14px 18px 16px;
        }

        .trend-chart-wrap {
          min-width: 0;
          border-radius: 12px;
          background: rgba(3, 13, 15, 0.34);
          border: 1px solid rgba(255, 255, 255, 0.05);
          padding: 10px 10px 2px;
        }

        .trend-chart {
          display: block;
          width: 100%;
          height: 275px;
          overflow: visible;
        }

        .trend-grid-line {
          stroke: rgba(175, 205, 202, 0.12);
          stroke-width: 1;
        }

        .trend-axis-line {
          stroke: rgba(215, 230, 228, 0.24);
          stroke-width: 1;
        }

        .trend-axis-label {
          fill: rgba(225, 237, 235, 0.6);
          font-size: 11px;
          font-weight: 600;
        }

        .trend-area {
          fill: rgba(52, 238, 182, 0.1);
        }

        .trend-line {
          fill: none;
          stroke: var(--mint);
          stroke-width: 3;
          stroke-linecap: round;
          stroke-linejoin: round;
          filter: drop-shadow(0 0 6px rgba(52, 238, 182, 0.18));
        }

        .trend-point {
          fill: var(--mint);
          stroke: rgba(4, 18, 19, 0.94);
          stroke-width: 2;
        }

        .trend-summary {
          display: flex;
          flex-direction: column;
          gap: 12px;
          border-left: 1px solid rgba(255, 255, 255, 0.08);
          padding-left: 16px;
        }

        .trend-summary-block {
          display: flex;
          flex-direction: column;
          gap: 3px;
        }

        .trend-summary-label {
          color: rgba(235, 243, 242, 0.54);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.07em;
          text-transform: uppercase;
        }

        .trend-summary-value {
          color: rgba(248, 251, 250, 0.96);
          font-size: 17px;
          font-weight: 800;
        }

        .trend-summary-value.accent {
          color: var(--mint);
          font-size: 22px;
        }

        .trend-summary-sub {
          color: rgba(235, 243, 242, 0.5);
          font-size: 11px;
        }

        .trend-stat-row {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 10px;
          padding: 0 18px 18px;
        }

        .trend-mini-stat {
          padding: 12px 14px;
          border-radius: 11px;
          border: 1px solid rgba(255, 255, 255, 0.06);
          background: rgba(5, 15, 17, 0.52);
        }

        .trend-mini-stat strong {
          display: block;
          margin-bottom: 2px;
          color: rgba(248, 251, 250, 0.96);
          font-size: 15px;
        }

        .trend-mini-stat span {
          color: rgba(235, 243, 242, 0.5);
          font-size: 10px;
        }

        .trend-empty {
          min-height: 295px;
          display: flex;
          align-items: center;
          justify-content: center;
          text-align: center;
          color: rgba(235, 243, 242, 0.52);
          padding: 30px;
        }

        @media (max-width: 1350px) {
          .trend-chart-layout {
            grid-template-columns: 1fr;
          }

          .trend-summary {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            border-left: 0;
            border-top: 1px solid rgba(255, 255, 255, 0.08);
            padding: 14px 0 0;
          }
        }

        @media (max-width: 980px) {
          .price-trend-panel .panel-header {
            align-items: flex-start;
            flex-direction: column;
          }

          .trend-controls {
            width: 100%;
            margin-left: 0;
          }

          .trend-select {
            flex: 1;
            min-width: 0;
          }

          .trend-summary,
          .trend-stat-row {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }
        }

        @media (max-width: 620px) {
          .trend-controls {
            flex-direction: column;
            align-items: stretch;
          }

          .trend-summary,
          .trend-stat-row {
            grid-template-columns: 1fr;
          }

          .trend-chart {
            height: 240px;
          }
        }
      `}</style>
<section className="stat-grid dashboard-stat-grid">
          <StatCard
            icon="■"
            title="Tracked Products"
            value={String(trackedCount)}
            subtitle="Products you're watching"
            details={[
              { label: "Price checked", value: String(trackedBreakdown.checked) },
              { label: "Targets set", value: String(trackedBreakdown.withTargets) },
              { label: "Stores", value: String(trackedBreakdown.stores) },
            ]}
          />

          <StatCard
            icon="◆"
            title="Price Drops"
            value={String(priceDropProducts.length)}
            subtitle={priceDropProducts.length ? "Recorded drops across your Wishlist" : "No recorded price drops yet"}
            details={[
              {
                label: "Biggest drop",
                value: biggestPriceDrop.product ? compactMoney(biggestPriceDrop.drop) : "—",
                accent: Boolean(biggestPriceDrop.product),
              },
              {
                label: "Product",
                value: biggestPriceDrop.product?.displayName ?? "None yet",
              },
              {
                label: "Watching",
                value: `${trackedCount} product${trackedCount === 1 ? "" : "s"}`,
              },
            ]}
          />

          <StatCard
            icon="★"
            title="Hottest Product"
            value={hottestProduct.product ? `${compactMoney(hottestProduct.saving)} saved` : "$0 saved"}
            subtitle={
              hottestProduct.product
                ? hottestProduct.source === "PRICE_DROP"
                  ? "Leading recorded price drop"
                  : "Best saving against target"
                : "No target savings or price drops yet"
            }
            details={[
              { label: "Product", value: hottestProduct.product?.displayName ?? "None yet" },
              {
                label: "Current",
                value: hottestProduct.product ? money(hottestProduct.product.currentPrice) : "—",
              },
              {
                label: "Target",
                value: hottestProduct.product ? money(hottestProduct.product.targetPrice) : "—",
                accent: Boolean(hottestProduct.product && hottestProduct.saving > 0),
              },
            ]}
            tone="amber"
          />

          <StatCard
            icon="!"
            title="Active Alerts"
            value={String(activeAlertCount)}
            subtitle="Products with alerts enabled"
            href="/alerts"
            details={[
              { label: "Target alerts", value: String(alertBreakdown.target) },
              { label: "Price drops", value: String(alertBreakdown.drops) },
              { label: "Digests", value: String(alertBreakdown.digest) },
            ]}
            tone="blue"
          />
        </section>

        <section className="content-grid recent-products-layout">
          <article className="glass-card panel recent-products-panel">
            <div className="panel-header">
              <div className="panel-title">
                <span className="panel-title-icon">◆</span>
                <h3>Recent Products</h3>
              </div>

              <div className="panel-actions">
                <label className="sort-control">
                  <span>Sort by</span>

                  <select
                    value={sort}
                    onChange={(event) => setSort(event.target.value)}
                  >
                    <option value="recent">Recent products</option>
                    <option value="cheapest">Cheapest products</option>
                    <option value="savings">Biggest savings</option>
                    <option value="name">Product name</option>
                  </select>
                </label>

                <Link href="/products" className="text-link">
                  View all ›
                </Link>
              </div>
            </div>

            <div
              className="drop-list"
              style={{
                maxHeight: "430px",
                overflowY: "auto",
                overflowX: "hidden",
                scrollbarGutter: "stable",
              }}
            >
              {loadError ? (
                <div
                  style={{
                    padding: "28px",
                    color: "rgba(240,245,245,0.72)",
                  }}
                >
                  {loadError}
                </div>
              ) : null}

              {!loadError && recentProducts.length === 0 ? (
                <div
                  style={{
                    padding: "34px 28px",
                    color: "rgba(240,245,245,0.58)",
                  }}
                >
                  {products.length === 0
                    ? "No products are being tracked yet."
                    : "No tracked products match your search."}
                </div>
              ) : null}

              {recentProducts.map((product) => {
                const saving =
                  product.currentPrice !== null && product.addedPrice !== null
                    ? product.addedPrice - product.currentPrice
                    : null;

                const savingPercent =
                  saving !== null &&
                  saving > 0 &&
                  product.addedPrice !== null &&
                  product.addedPrice > 0
                    ? Math.round((saving / product.addedPrice) * 100)
                    : null;

                const targetDifference = toTarget(product);
                const targetReached =
                  targetDifference !== null && targetDifference <= 0;

                return (
                  <div
                    className="drop-row"
                    key={product.id}
                    style={{
                      gridTemplateColumns:
                        "54px minmax(220px, 1.7fr) minmax(90px, 0.75fr) minmax(90px, 0.75fr) minmax(95px, 0.8fr) minmax(92px, 0.75fr) auto",
                      columnGap: "16px",
                      alignItems: "center",
                    }}
                  >
                    <ProductThumb product={product} />

                    <div className="product-copy">
                      <strong>{product.displayName}</strong>
                      <span>
                        {product.store}
                        {product.category ? ` · ${product.category}` : ""}
                      </span>
                    </div>

                    <div className="recent-metric">
                      <span className="recent-metric-label">Current</span>
                      <strong className="new-price">
                        {money(product.currentPrice)}
                      </strong>
                    </div>

                    <div className="recent-metric">
                      <span className="recent-metric-label">Target</span>
                      <strong>{money(product.targetPrice)}</strong>
                    </div>

                    <div className="recent-metric">
                      <span className="recent-metric-label">To target</span>
                      <strong
                        style={{
                          color:
                            targetDifference === null
                              ? "rgba(235,243,242,0.52)"
                              : targetReached
                                ? "var(--mint)"
                                : "#ff8f73",
                        }}
                      >
                        {targetDifference === null
                          ? "—"
                          : `${targetDifference > 0 ? "+" : "-"}${compactMoney(
                              Math.abs(targetDifference),
                            )}`}
                      </strong>
                    </div>

                    <div className="recent-alert-status">
                      <span
                        className="recent-alert-dot"
                        style={{
                          background:
                            product.alertSettings?.mode === "OFF"
                              ? "rgba(235,243,242,0.25)"
                              : "var(--mint)",
                          boxShadow:
                            product.alertSettings?.mode === "OFF"
                              ? "none"
                              : "0 0 12px rgba(52, 238, 182, 0.65)",
                        }}
                      />
                      <span>{alertLabel(product.alertSettings?.mode)}</span>
                    </div>

                    <div className="recent-row-tail">
                      {savingPercent !== null ? (
                        <span className="drop-badge">
                          ↓ {savingPercent}% · {compactMoney(saving ?? 0)}
                        </span>
                      ) : null}

                      <Link
                        href="/products"
                        className="row-open"
                        aria-label={`Open ${product.displayName}`}
                      >
                        ›
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          </article>

          <article className="glass-card panel price-trend-panel">
            <div className="panel-header">
              <div className="panel-title">
                <span className="panel-title-icon">▥</span>
                <h3>Price Trend</h3>
              </div>

              <div className="trend-controls">
                <select
                  className="trend-select"
                  value={trendProduct?.id ?? ""}
                  onChange={(event) => setTrendProductId(event.target.value)}
                  aria-label="Choose product for price trend"
                >
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.displayName}
                    </option>
                  ))}
                </select>

                <select
                  className="trend-select range"
                  value={trendRange}
                  onChange={(event) => setTrendRange(event.target.value)}
                  aria-label="Choose price trend time range"
                >
                  <option value="1">Last month</option>
                  <option value="3">Last 3 months</option>
                  <option value="6">Last 6 months</option>
                  <option value="12">Last 12 months</option>
                  <option value="all">All history</option>
                </select>
              </div>
            </div>

            {!trendProduct || trendData.points.length === 0 ? (
              <div className="trend-empty">
                No price history is available for this product yet.
              </div>
            ) : (
              <>
                <div className="trend-chart-layout">
                  <div className="trend-chart-wrap">
                    <svg
                      className="trend-chart"
                      viewBox="0 0 820 300"
                      role="img"
                      aria-label={`Price history for ${trendProduct.displayName}`}
                    >
                      {chartGeometry.yTicks.map((tick, index) => {
                        const top = 18;
                        const bottom = 42;
                        const height = 300;
                        const innerHeight = height - top - bottom;
                        const y =
                          top +
                          (index / Math.max(chartGeometry.yTicks.length - 1, 1)) *
                            innerHeight;

                        return (
                          <g key={`${tick}-${index}`}>
                            <line
                              className="trend-grid-line"
                              x1="62"
                              x2="802"
                              y1={y}
                              y2={y}
                            />
                            <text
                              className="trend-axis-label"
                              x="54"
                              y={y + 4}
                              textAnchor="end"
                            >
                              {compactMoney(tick)}
                            </text>
                          </g>
                        );
                      })}

                      {chartGeometry.plotted.map((entry, index) => {
                        const shouldLabel =
                          chartGeometry.plotted.length <= 7 ||
                          index === 0 ||
                          index === chartGeometry.plotted.length - 1 ||
                          index % Math.ceil(chartGeometry.plotted.length / 6) === 0;

                        if (!shouldLabel) return null;

                        return (
                          <g key={`x-label-${entry.point.checkedAt}-${index}`}>
                            <line
                              className="trend-grid-line"
                              x1={entry.x}
                              x2={entry.x}
                              y1="18"
                              y2="258"
                            />
                            <text
                              className="trend-axis-label"
                              x={entry.x}
                              y="281"
                              textAnchor="middle"
                            >
                              {monthLabel(entry.point.checkedAt)}
                            </text>
                          </g>
                        );
                      })}

                      <line
                        className="trend-axis-line"
                        x1="62"
                        x2="802"
                        y1="258"
                        y2="258"
                      />

                      {chartGeometry.area ? (
                        <path className="trend-area" d={chartGeometry.area} />
                      ) : null}

                      <path className="trend-line" d={chartGeometry.line} />

                      {chartGeometry.plotted.map((entry, index) => (
                        <circle
                          key={`${entry.point.checkedAt}-${index}`}
                          className="trend-point"
                          cx={entry.x}
                          cy={entry.y}
                          r="5"
                        >
                          <title>
                            {`${shortDate(entry.point.checkedAt)} — ${money(
                              entry.point.price,
                            )}`}
                          </title>
                        </circle>
                      ))}

                      <text
                        className="trend-axis-label"
                        x="16"
                        y="150"
                        textAnchor="middle"
                        transform="rotate(-90 16 150)"
                      >
                        Price (AUD)
                      </text>
                    </svg>
                  </div>

                  <aside className="trend-summary">
                    <div className="trend-summary-block">
                      <span className="trend-summary-label">Current price</span>
                      <strong className="trend-summary-value accent">
                        {money(trendProduct.currentPrice)}
                      </strong>
                      <span className="trend-summary-sub">
                        {trendProduct.targetPrice !== null &&
                        trendProduct.currentPrice !== null
                          ? `${
                              trendProduct.currentPrice <= trendProduct.targetPrice
                                ? "Below"
                                : "Above"
                            } target by ${compactMoney(
                              Math.abs(
                                trendProduct.currentPrice -
                                  trendProduct.targetPrice,
                              ),
                            )}`
                          : "No target set"}
                      </span>
                    </div>

                    <div className="trend-summary-block">
                      <span className="trend-summary-label">Target price</span>
                      <strong className="trend-summary-value">
                        {money(trendProduct.targetPrice)}
                      </strong>
                    </div>

                    <div className="trend-summary-block">
                      <span className="trend-summary-label">Lowest price</span>
                      <strong className="trend-summary-value">
                        {trendData.lowest ? money(trendData.lowest.price) : "—"}
                      </strong>
                      <span className="trend-summary-sub">
                        {trendData.lowest ? shortDate(trendData.lowest.checkedAt) : ""}
                      </span>
                    </div>

                    <div className="trend-summary-block">
                      <span className="trend-summary-label">Highest price</span>
                      <strong className="trend-summary-value">
                        {trendData.highest ? money(trendData.highest.price) : "—"}
                      </strong>
                      <span className="trend-summary-sub">
                        {trendData.highest
                          ? shortDate(trendData.highest.checkedAt)
                          : ""}
                      </span>
                    </div>
                  </aside>
                </div>

                <div className="trend-stat-row">
                  <div className="trend-mini-stat">
                    <strong>
                      {trendData.average !== null
                        ? money(trendData.average)
                        : "—"}
                    </strong>
                    <span>Average price</span>
                  </div>

                  <div className="trend-mini-stat">
                    <strong
                      style={{
                        color:
                          trendData.totalChange !== null &&
                          trendData.totalChange < 0
                            ? "var(--mint)"
                            : trendData.totalChange !== null &&
                                trendData.totalChange > 0
                              ? "#ff8f73"
                              : undefined,
                      }}
                    >
                      {trendData.totalChange === null
                        ? "—"
                        : `${trendData.totalChange > 0 ? "+" : ""}${money(
                            trendData.totalChange,
                          )}`}
                    </strong>
                    <span>Total change</span>
                  </div>

                  <div className="trend-mini-stat">
                    <strong>{trendData.points.length}</strong>
                    <span>Price checks</span>
                  </div>

                  <div className="trend-mini-stat">
                    <strong>
                      {trendData.percentChange === null
                        ? "—"
                        : `${trendData.percentChange > 0 ? "+" : ""}${trendData.percentChange.toFixed(
                            1,
                          )}%`}
                    </strong>
                    <span>Change</span>
                  </div>
                </div>
              </>
            )}
          </article>
        </section>

        <footer className="dashboard-footer">
          <span>© 2026 Wishlist. Pick a WishList. Get a Bargain.</span>

          <div>
            <button>Privacy</button>
            <button>Terms</button>
            <button>Contact</button>
          </div>
        </footer>
    </>
  );
}