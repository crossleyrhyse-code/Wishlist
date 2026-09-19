"use client";

import { useEffect, useMemo, useState } from "react";
import { loadWishlistProducts } from "../data/wishlistProducts";


type WishlistProduct = {
  id: string;
  displayName: string;
  name: string;
  store: string;
  imageUrl: string | null;
  currentPrice: number | null;
  targetPrice: number | null;

  notificationPending?: boolean;
  notificationTriggeredAt?: string | null;
  notificationReason?: string | null;
};

function money(value: number | null) {
  if (value === null) return "—";

  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

function alertReason(reason?: string | null) {
  switch (reason) {
    case "TARGET_REACHED":
      return "Target price reached";

    case "PRICE_DROP":
      return "Price dropped";

    case "PRICE_CHANGE":
      return "Price changed";

    default:
      return "Price alert";
  }
}

function formatDate(value: string) {
  return new Intl.DateTimeFormat("en-AU", {
    day: "numeric",
    month: "short",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

export default function AlertsPage() {
  const [products, setProducts] =
    useState<WishlistProduct[]>([]);

  const [loadError, setLoadError] = useState("");

  useEffect(() => {
    async function loadProducts() {
      try {
        const data = (await loadWishlistProducts()) as WishlistProduct[];
        setProducts(data);
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

  const alerts = useMemo(
    () =>
      products
        .filter(
          (product) => product.notificationTriggeredAt,
        )
        .sort(
          (a, b) =>
            new Date(
              b.notificationTriggeredAt ?? 0,
            ).getTime() -
            new Date(
              a.notificationTriggeredAt ?? 0,
            ).getTime(),
        ),
    [products],
  );

  return (
    <>
      <style jsx global>{`
        .alerts-page {
          padding-bottom: 40px;
        }

        .alerts-header {
          margin-bottom: 24px;
        }

        .alerts-header h2 {
          margin: 4px 0 5px;
          font-size: 30px;
        }

        .alerts-header p {
          margin: 0;
          color: rgba(235, 243, 242, 0.55);
        }

        .alerts-card {
          overflow: hidden;
        }

        .alerts-card-heading {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 18px 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        }

        .alerts-card-heading h3 {
          margin: 0;
        }

        .alerts-count {
          min-width: 26px;
          height: 26px;
          padding: 0 8px;
          display: flex;
          align-items: center;
          justify-content: center;
          border-radius: 999px;
          background: rgba(52, 238, 182, 0.1);
          border: 1px solid rgba(52, 238, 182, 0.16);
          color: var(--mint);
          font-size: 11px;
          font-weight: 800;
        }

        .alert-list {
          display: flex;
          flex-direction: column;
        }

        .alert-row {
          display: grid;
          grid-template-columns: 54px minmax(0, 1fr) auto;
          gap: 14px;
          align-items: center;
          padding: 16px 20px;
          border-bottom: 1px solid rgba(255, 255, 255, 0.055);
        }

        .alert-row:last-child {
          border-bottom: 0;
        }

        .alert-image {
          width: 52px;
          height: 52px;
          border-radius: 11px;
          overflow: hidden;
          display: flex;
          align-items: center;
          justify-content: center;
          background: rgba(255, 255, 255, 0.04);
          border: 1px solid rgba(255, 255, 255, 0.07);
        }

        .alert-image img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .alert-main {
          min-width: 0;
        }

        .alert-topline {
          display: flex;
          gap: 8px;
          align-items: center;
          margin-bottom: 4px;
        }

        .alert-dot {
          width: 8px;
          height: 8px;
          border-radius: 999px;
          background: var(--mint);
          box-shadow: 0 0 8px rgba(52, 238, 182, 0.55);
        }

        .alert-main strong {
          display: block;
          margin-bottom: 3px;
        }

        .alert-product-name {
          color: rgba(235, 243, 242, 0.7);
          font-size: 12px;
        }

        .alert-store {
          color: rgba(235, 243, 242, 0.42);
          font-size: 10px;
          text-transform: uppercase;
          letter-spacing: 0.06em;
          font-weight: 700;
        }

        .alert-details {
          display: flex;
          gap: 28px;
          align-items: center;
        }

        .alert-detail {
          display: flex;
          flex-direction: column;
          text-align: right;
          gap: 3px;
        }

        .alert-detail span {
          color: rgba(235, 243, 242, 0.42);
          font-size: 9px;
          font-weight: 800;
          letter-spacing: 0.07em;
          text-transform: uppercase;
        }

        .alert-detail strong {
          font-size: 12px;
          white-space: nowrap;
        }

        .alert-detail strong.green {
          color: var(--mint);
        }

        .alerts-empty {
          min-height: 350px;
          display: flex;
          align-items: center;
          justify-content: center;
          flex-direction: column;
          text-align: center;
          gap: 7px;
          color: rgba(235, 243, 242, 0.47);
        }

        .alerts-empty-icon {
          width: 54px;
          height: 54px;
          border-radius: 16px;
          background: rgba(255, 255, 255, 0.035);
          border: 1px solid rgba(255, 255, 255, 0.06);
          display: flex;
          align-items: center;
          justify-content: center;
          margin-bottom: 6px;
          font-size: 20px;
        }

        .alerts-empty strong {
          color: rgba(245, 249, 248, 0.92);
          font-size: 17px;
        }

        @media (max-width: 900px) {
          .alert-row {
            grid-template-columns: 54px minmax(0, 1fr);
          }

          .alert-details {
            grid-column: 2;
            justify-content: flex-start;
          }

          .alert-detail {
            text-align: left;
          }
        }
      `}</style>

      <section className="alerts-page">
          <header className="alerts-header">
            <span className="eyebrow">NOTIFICATIONS</span>

            <h2>Alerts</h2>

            <p>
              Price alerts from your tracked products will appear
              here.
            </p>
          </header>

          <section className="glass-card alerts-card">
            <div className="alerts-card-heading">
              <h3>Recent Alerts</h3>

              {alerts.length > 0 && (
                <span className="alerts-count">
                  {alerts.length}
                </span>
              )}
            </div>

            {loadError ? (
              <div className="alerts-empty">
                <div className="alerts-empty-icon">!</div>

                <strong>Could not load alerts</strong>

                <span>{loadError}</span>
              </div>
            ) : alerts.length === 0 ? (
              <div className="alerts-empty">
                <div className="alerts-empty-icon">♢</div>

                <strong>No alerts</strong>

                <span>
                  New price alerts will appear here.
                </span>
              </div>
            ) : (
              <div className="alert-list">
                {alerts.map((product) => (
                  <div
                    className="alert-row"
                    key={`${product.id}-${product.notificationTriggeredAt}`}
                  >
                    <div className="alert-image">
                      {product.imageUrl ? (
                        <img
                          src={product.imageUrl}
                          alt={product.displayName}
                          referrerPolicy="no-referrer"
                        />
                      ) : (
                        <span>◫</span>
                      )}
                    </div>

                    <div className="alert-main">
                      <div className="alert-topline">
                        <span className="alert-dot" />

                        <strong>
                          {alertReason(
                            product.notificationReason,
                          )}
                        </strong>
                      </div>

                      <div className="alert-product-name">
                        {product.displayName ??
                          product.name}
                      </div>

                      <div className="alert-store">
                        {product.store}
                      </div>
                    </div>

                    <div className="alert-details">
                      <div className="alert-detail">
                        <span>Current Price</span>

                        <strong className="green">
                          {money(product.currentPrice)}
                        </strong>
                      </div>

                      <div className="alert-detail">
                        <span>Target</span>

                        <strong>
                          {money(product.targetPrice)}
                        </strong>
                      </div>

                      <div className="alert-detail">
                        <span>Triggered</span>

                        <strong>
                          {product.notificationTriggeredAt
                            ? formatDate(
                                product.notificationTriggeredAt,
                              )
                            : "—"}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>
        </section>
    </>
  );
}