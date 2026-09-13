"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  checkWishlistProductPrice,
  deleteWishlistProduct,
  loadWishlistProducts,
  updateWishlistProduct,
} from "../data/wishlistProducts";

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

function alertModeLabel(mode: AlertMode) {
  const labels: Record<AlertMode, string> = {
    TARGET_REACHED: "Target price reached",
    PRICE_DROP: "Every price drop",
    PRICE_CHANGE: "Every price change",
    DAILY_DIGEST: "Daily summary",
    WEEKLY_DIGEST: "Weekly summary",
    OFF: "Off",
  };

  return labels[mode];
}

function signedMoney(value: number) {
  const absoluteValue = Math.abs(value);

  const formatted = new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(absoluteValue);

  if (value > 0) return `+${formatted}`;
  if (value < 0) return `-${formatted}`;

  return formatted;
}

export default function ProductsPage() {
  const [products, setProducts] = useState<WishlistProduct[]>([]);
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("recent");
  const [checkingProductId, setCheckingProductId] = useState<string | null>(null);
  const [deletingProductId, setDeletingProductId] = useState<string | null>(null);
  const [editingTargetId, setEditingTargetId] = useState<string | null>(null);
  const [targetDraft, setTargetDraft] = useState("");
  const [savingTargetId, setSavingTargetId] = useState<string | null>(null);
  const [alertMenuId, setAlertMenuId] = useState<string | null>(null);
  const [savingAlertId, setSavingAlertId] = useState<string | null>(null);
  const [alertErrors, setAlertErrors] = useState<Record<string, string>>({});
  const [priceErrors, setPriceErrors] = useState<Record<string, string>>({});
  const [loadError, setLoadError] = useState("");

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

  async function checkPrice(product: WishlistProduct) {
    setCheckingProductId(product.id);
    setPriceErrors((current) => ({ ...current, [product.id]: "" }));

    try {
      const updatedProduct = (await checkWishlistProductPrice(
        product,
      )) as WishlistProduct;

      setProducts((current) =>
        current.map((savedProduct) =>
          savedProduct.id === product.id
            ? updatedProduct
            : savedProduct,
        ),
      );
    } catch (error) {
      setPriceErrors((current) => ({
        ...current,
        [product.id]:
          error instanceof Error ? error.message : "Price check failed.",
      }));
    } finally {
      setCheckingProductId(null);
    }
  }

  function startEditingTarget(product: WishlistProduct) {
    setEditingTargetId(product.id);
    setTargetDraft(
      product.targetPrice !== null
        ? product.targetPrice.toString()
        : "",
    );
  }

  function cancelEditingTarget() {
    setEditingTargetId(null);
    setTargetDraft("");
  }

  async function saveTargetPrice(product: WishlistProduct) {
    const trimmedValue = targetDraft.trim();

    const newTarget =
      trimmedValue === ""
        ? null
        : Number(trimmedValue);

    if (
      newTarget !== null &&
      (!Number.isFinite(newTarget) || newTarget < 0)
    ) {
      window.alert("Please enter a valid target price.");
      return;
    }

    setSavingTargetId(product.id);

    try {
      const updatedProduct = (await updateWishlistProduct(product.id, {
        targetPrice: newTarget,
      })) as WishlistProduct;

      setProducts((current) =>
        current.map((savedProduct) =>
          savedProduct.id === product.id
            ? updatedProduct
            : savedProduct,
        ),
      );

      setEditingTargetId(null);
      setTargetDraft("");
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : "Could not update target price.",
      );
    } finally {
      setSavingTargetId(null);
    }
  }

  async function updateAlertSettings(
    product: WishlistProduct,
    mode: AlertMode,
    emailEnabled: boolean,
  ) {
    setSavingAlertId(product.id);
    setAlertErrors((current) => ({ ...current, [product.id]: "" }));

    try {
      const updatedProduct = (await updateWishlistProduct(product.id, {
        alertSettings: {
          mode,
          emailEnabled,
        },
      })) as WishlistProduct;

      setProducts((current) =>
        current.map((savedProduct) =>
          savedProduct.id === product.id ? updatedProduct : savedProduct,
        ),
      );

      if (mode !== product.alertSettings?.mode) {
        setAlertMenuId(null);
      }
    } catch (error) {
      setAlertErrors((current) => ({
        ...current,
        [product.id]:
          error instanceof Error
            ? error.message
            : "Could not update alert settings.",
      }));
    } finally {
      setSavingAlertId(null);
    }
  }

  async function removeProduct(product: WishlistProduct) {
    const confirmed = window.confirm(
      `Are you sure you want to remove "${product.displayName}" from your Wishlist?`,
    );

    if (!confirmed) {
      return;
    }

    setDeletingProductId(product.id);

    try {
      await deleteWishlistProduct(product.id);

      setProducts((current) =>
        current.filter((savedProduct) => savedProduct.id !== product.id),
      );
    } catch (error) {
      window.alert(
        error instanceof Error
          ? error.message
          : "Could not remove this product.",
      );
    } finally {
      setDeletingProductId(null);
    }
  }

  const visibleProducts = useMemo(() => {
    const filtered = products.filter((product) => {
      const haystack =
        `${product.displayName} ${product.name} ${product.store} ${product.category}`.toLowerCase();

      return haystack.includes(search.toLowerCase());
    });

    return [...filtered].sort((a, b) => {
      if (sort === "cheapest") {
        if (a.currentPrice === null && b.currentPrice === null) return 0;
        if (a.currentPrice === null) return 1;
        if (b.currentPrice === null) return -1;
        return a.currentPrice - b.currentPrice;
      }

      if (sort === "saving") {
        const aSaving =
          a.currentPrice !== null && a.addedPrice !== null
            ? a.addedPrice - a.currentPrice
            : null;

        const bSaving =
          b.currentPrice !== null && b.addedPrice !== null
            ? b.addedPrice - b.currentPrice
            : null;

        if (aSaving === null && bSaving === null) return 0;
        if (aSaving === null) return 1;
        if (bSaving === null) return -1;

        return bSaving - aSaving;
      }

      if (sort === "name") {
        return a.displayName.localeCompare(b.displayName);
      }

      return b.addedOrder - a.addedOrder;
    });
  }, [products, search, sort]);

  return (
<section className="products-dashboard">
        <header className="products-header">
          <div>
            <span className="eyebrow">YOUR WISHLIST</span>
            <h2>My Products</h2>
            <p>Everything you are tracking in one place.</p>
          </div>

          <div className="products-header-actions">
            <label className="search-box products-search">
              <span className="search-icon">⌕</span>
              <input
                type="search"
                placeholder="Search products, brands or stores..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>

            <Link href="/products/add" className="add-product-button">
              <span>＋</span>
              Add Product
            </Link>
          </div>
        </header>

        <section className="glass-card products-panel">
          <div className="products-panel-header">
            <div>
              <h3>Tracked Products</h3>
              <span>{visibleProducts.length} products shown</span>
            </div>

            <label className="products-sort">
              <span>Sort</span>
              <select
                value={sort}
                onChange={(event) => setSort(event.target.value)}
              >
                <option value="recent">Recent products</option>
                <option value="cheapest">Cheapest products</option>
                <option value="saving">Biggest savings</option>
                <option value="name">Product name</option>
              </select>
            </label>
          </div>

          <div className="products-list pretty-products-list">
            {loadError ? (
              <div style={{ padding: "24px", opacity: 0.7 }}>
                {loadError}
              </div>
            ) : null}

            {visibleProducts.map((product) => {
              const saving =
                product.currentPrice !== null && product.addedPrice !== null
                  ? product.addedPrice - product.currentPrice
                  : null;

              const savingPercent =
                saving !== null &&
                product.addedPrice !== null &&
                product.addedPrice > 0
                  ? Math.round((saving / product.addedPrice) * 100)
                  : null;

              const targetGap =
                product.currentPrice !== null &&
                product.targetPrice !== null
                  ? product.currentPrice - product.targetPrice
                  : null;

              return (
                <article
                  className={`product-card-row pretty-product-row ${
                    alertMenuId === product.id ? "alert-menu-open" : ""
                  }`}
                  key={product.id}
                >
                  <div className="product-thumb products-thumb pretty-product-thumb">
                    {product.imageUrl ? (
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
                    ) : (
                      <span>◫</span>
                    )}
                  </div>

                  <div className="products-main-copy">
                    <strong>{product.displayName}</strong>
                    <span>
                      {product.store} · {product.category}
                    </span>
                  </div>

                  <div className="product-metric pretty-product-metric">
                    <span>CURRENT</span>
                    <strong
                      style={{
                        color:
                          product.currentPrice === null
                            ? "rgba(231, 239, 239, 0.5)"
                            : undefined,
                      }}
                    >
                      {checkingProductId === product.id
                        ? "Checking..."
                        : money(product.currentPrice)}
                    </strong>
                  </div>

                  <div className="product-metric pretty-product-metric">
                    <span>ADDED AT</span>
                    <strong
                      className={
                        product.addedPrice !== null ? "product-old-price" : ""
                      }
                      style={{
                        color:
                          product.addedPrice === null
                            ? "rgba(231, 239, 239, 0.5)"
                            : undefined,
                      }}
                    >
                      {money(product.addedPrice)}
                    </strong>
                  </div>

                  <div className="product-metric saving-metric pretty-product-metric">
                    <span>SAVING</span>
                    {saving !== null ? (
                      <>
                        <strong>{money(saving)}</strong>
                        {savingPercent !== null && savingPercent !== 0 && (
                          <small>
                            {savingPercent > 0 ? "↓" : "↑"}{" "}
                            {Math.abs(savingPercent)}%
                          </small>
                        )}
                      </>
                    ) : (
                      <strong
                        style={{ color: "rgba(231, 239, 239, 0.5)" }}
                      >
                        Waiting
                      </strong>
                    )}
                  </div>

                  <div className="product-metric pretty-product-metric target-price-cell">
                    <span>TARGET</span>

                    {editingTargetId === product.id ? (
                      <div className="target-edit-wrap">
                        <div className="target-input-wrap">
                          <span>$</span>

                          <input
                            type="number"
                            min="0"
                            step="0.01"
                            value={targetDraft}
                            onChange={(event) =>
                              setTargetDraft(event.target.value)
                            }
                            onKeyDown={(event) => {
                              if (event.key === "Enter") {
                                event.preventDefault();
                                saveTargetPrice(product);
                              }

                              if (event.key === "Escape") {
                                cancelEditingTarget();
                              }
                            }}
                            autoFocus
                          />
                        </div>

                        <div className="target-edit-actions">
                          <button
                            type="button"
                            className="target-save-button"
                            onClick={() => saveTargetPrice(product)}
                            disabled={savingTargetId === product.id}
                          >
                            {savingTargetId === product.id
                              ? "Saving..."
                              : "Save"}
                          </button>

                          <button
                            type="button"
                            className="target-cancel-button"
                            onClick={cancelEditingTarget}
                            disabled={savingTargetId === product.id}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="target-display-wrap">
                        <strong>{money(product.targetPrice)}</strong>

                        <button
                          type="button"
                          className="target-edit-button"
                          onClick={() => startEditingTarget(product)}
                          title="Change target price"
                          aria-label={`Change target price for ${product.displayName}`}
                        >
                          <svg
                            width="16"
                            height="16"
                            viewBox="0 0 24 24"
                            fill="none"
                            xmlns="http://www.w3.org/2000/svg"
                            aria-hidden="true"
                          >
                            <path
                              d="M4 20L8.5 19L18.5 9L15 5.5L5 15.5L4 20Z"
                              stroke="currentColor"
                              strokeWidth="1.8"
                              strokeLinejoin="round"
                            />
                            <path
                              d="M13.8 6.7L17.3 10.2"
                              stroke="currentColor"
                              strokeWidth="1.8"
                            />
                          </svg>
                        </button>
                      </div>
                    )}
                  </div>

                  <div className="product-metric pretty-product-metric target-gap-cell">
                    <span>TO TARGET</span>

                    {targetGap === null ? (
                      <strong className="target-gap-neutral">—</strong>
                    ) : (
                      <strong
                        className={
                          targetGap <= 0
                            ? "target-gap-reached"
                            : "target-gap-above"
                        }
                        title={
                          targetGap <= 0
                            ? "Current price is at or below your target"
                            : "Current price is still above your target"
                        }
                      >
                        {signedMoney(targetGap)}
                      </strong>
                    )}
                  </div>

                  <div className="alert-control-wrap">
                    <button
                      type="button"
                      className={`alert-settings-button ${
                        (product.alertSettings?.mode ?? "TARGET_REACHED") !== "OFF"
                          ? "on"
                          : "off"
                      }`}
                      title={`Alerts: ${alertModeLabel(
                        product.alertSettings?.mode ?? "TARGET_REACHED",
                      )}`}
                      aria-label={`Change alert settings for ${product.displayName}`}
                      onClick={() =>
                        setAlertMenuId((current) =>
                          current === product.id ? null : product.id,
                        )
                      }
                    >
                      <span className="alert-settings-dot" />
                    </button>

                    {alertMenuId === product.id ? (
                      <div className="alert-settings-popover">
                        <div className="alert-popover-heading">
                          <div>
                            <strong>Alert me when</strong>
                            <span>Choose how this product notifies you.</span>
                          </div>

                          <button
                            type="button"
                            className="alert-popover-close"
                            onClick={() => setAlertMenuId(null)}
                            aria-label="Close alert settings"
                          >
                            ×
                          </button>
                        </div>

                        <div className="alert-mode-list">
                          {([
                            ["TARGET_REACHED", "Target price reached", "Recommended"],
                            ["PRICE_DROP", "Every price drop", ""],
                            ["PRICE_CHANGE", "Every price change", ""],
                            ["DAILY_DIGEST", "Daily summary", "One email summary each day"],
                            ["WEEKLY_DIGEST", "Weekly summary", "One email summary each week"],
                          ] as const).map(([mode, label, note]) => {
                            const selected =
                              (product.alertSettings?.mode ?? "TARGET_REACHED") === mode;

                            return (
                              <button
                                type="button"
                                className={`alert-mode-option ${
                                  selected ? "selected" : ""
                                }`}
                                key={mode}
                                disabled={savingAlertId === product.id}
                                onClick={() =>
                                  updateAlertSettings(
                                    product,
                                    mode,
                                    product.alertSettings?.emailEnabled ?? true,
                                  )
                                }
                              >
                                <span className="alert-radio">
                                  {selected ? "●" : "○"}
                                </span>
                                <span className="alert-option-copy">
                                  <strong>{label}</strong>
                                  {note ? <small>{note}</small> : null}
                                </span>
                              </button>
                            );
                          })}

                          <button
                            type="button"
                            className={`alert-mode-option ${
                              (product.alertSettings?.mode ?? "TARGET_REACHED") ===
                              "OFF"
                                ? "selected"
                                : ""
                            }`}
                            disabled={savingAlertId === product.id}
                            onClick={() =>
                              updateAlertSettings(
                                product,
                                "OFF",
                                product.alertSettings?.emailEnabled ?? true,
                              )
                            }
                          >
                            <span className="alert-radio">
                              {(product.alertSettings?.mode ?? "TARGET_REACHED") ===
                              "OFF"
                                ? "●"
                                : "○"}
                            </span>
                            <span className="alert-option-copy">
                              <strong>Off</strong>
                              <small>Keep tracking price without alerts</small>
                            </span>
                          </button>
                        </div>

                        <div className="alert-email-row">
                          <div>
                            <strong>Email notifications</strong>
                            <span>Send alerts to your email.</span>
                          </div>

                          <button
                            type="button"
                            className={`alert-email-toggle ${
                              product.alertSettings?.emailEnabled ?? true ? "on" : ""
                            }`}
                            disabled={savingAlertId === product.id}
                            onClick={() =>
                              updateAlertSettings(
                                product,
                                product.alertSettings?.mode ?? "TARGET_REACHED",
                                !(product.alertSettings?.emailEnabled ?? true),
                              )
                            }
                            aria-pressed={product.alertSettings?.emailEnabled ?? true}
                          >
                            <span />
                          </button>
                        </div>

                        {savingAlertId === product.id ? (
                          <div className="alert-save-status">Saving alert settings...</div>
                        ) : null}

                        {alertErrors[product.id] ? (
                          <div className="alert-save-error">
                            {alertErrors[product.id]}
                          </div>
                        ) : null}
                      </div>
                    ) : null}
                  </div>

                  <div className="product-row-actions pretty-product-actions">
                    <button
                      type="button"
                      className="product-action-link"
                      onClick={() => checkPrice(product)}
                      disabled={checkingProductId === product.id}
                      title={priceErrors[product.id] || "Check live price"}
                      style={{
                        cursor:
                          checkingProductId === product.id ? "wait" : "pointer",
                        opacity: checkingProductId === product.id ? 0.65 : 1,
                      }}
                    >
                      {checkingProductId === product.id
                        ? "Checking..."
                        : priceErrors[product.id]
                          ? "Retry Price"
                          : "Check Price"}
                    </button>

                    <Link href="/history" className="product-action-link">
                      History
                    </Link>

                    <Link href="/compare" className="product-action-link">
                      Compare
                    </Link>

                    <a
                      href={product.url}
                      target="_blank"
                      rel="noreferrer"
                      className="product-action-link"
                    >
                      Store
                    </a>

                    <button
                      type="button"
                      className="product-more pretty-trash-button"
                      aria-label={`Remove ${product.displayName}`}
                      title="Remove product"
                      onClick={() => removeProduct(product)}
                      disabled={deletingProductId === product.id}
                      style={{
                        cursor:
                          deletingProductId === product.id ? "wait" : "pointer",
                        opacity: deletingProductId === product.id ? 0.5 : 0.82,
                      }}
                    >
                      <svg
                        width="17"
                        height="17"
                        viewBox="0 0 24 24"
                        fill="none"
                        xmlns="http://www.w3.org/2000/svg"
                        aria-hidden="true"
                      >
                        <path
                          d="M4 7H20"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                        />
                        <path
                          d="M9 7V4.8C9 4.36 9.36 4 9.8 4H14.2C14.64 4 15 4.36 15 4.8V7"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                        />
                        <path
                          d="M6.5 7L7.3 19C7.35 19.56 7.82 20 8.38 20H15.62C16.18 20 16.65 19.56 16.7 19L17.5 7"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                        <path
                          d="M10 11V16"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                        />
                        <path
                          d="M14 11V16"
                          stroke="currentColor"
                          strokeWidth="1.8"
                          strokeLinecap="round"
                        />
                      </svg>
                    </button>
                  </div>
                </article>
              );
            })}
          </div>
        </section>


        <style jsx>{`
          .products-dashboard {
            padding-left: 22px !important;
            padding-right: 22px !important;
          }

          .products-panel {
            background: rgba(3, 13, 15, 0.90) !important;
            border: 1px solid rgba(255, 255, 255, 0.11);
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.035),
              0 18px 45px rgba(0, 0, 0, 0.24);
            backdrop-filter: blur(18px) saturate(108%);
            -webkit-backdrop-filter: blur(18px) saturate(108%);
            overflow: hidden;
          }

          .products-panel :global(.products-panel-header) {
            background: rgba(2, 12, 14, 0.97);
            border-bottom: 1px solid rgba(255, 255, 255, 0.075);
            box-shadow: 0 8px 20px rgba(0, 0, 0, 0.10);
          }

          .pretty-products-list {
            padding: 12px 8px 5px;
            background: rgba(2, 11, 13, 0.72);
          }

          .pretty-product-row {
            position: relative;
            grid-template-columns:
              68px
              minmax(205px, 1.65fr)
              92px
              92px
              86px
              118px
              88px
              22px
              minmax(320px, auto) !important;
            column-gap: 9px !important;
            padding-left: 10px !important;
            padding-right: 10px !important;
            margin-bottom: 12px;
            border: 1px solid rgba(255, 255, 255, 0.105);
            border-radius: 14px;
            background:
              linear-gradient(
                100deg,
                rgba(18, 31, 32, 0.66) 0%,
                rgba(23, 31, 30, 0.56) 52%,
                rgba(55, 48, 27, 0.42) 100%
              );
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.035),
              0 7px 20px rgba(0, 0, 0, 0.14);
            backdrop-filter: blur(7px);
            -webkit-backdrop-filter: blur(7px);
            overflow: hidden;
            transition:
              transform 160ms ease,
              border-color 160ms ease,
              background 160ms ease,
              box-shadow 160ms ease;
          }

          .pretty-product-row.alert-menu-open {
            z-index: 50;
            overflow: visible;
          }

          .alert-control-wrap {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 22px;
            z-index: 60;
          }

          .alert-settings-button {
            width: 30px;
            height: 30px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            padding: 0;
            border: 1px solid transparent;
            border-radius: 9px;
            background: transparent;
            cursor: pointer;
            transition:
              background 150ms ease,
              border-color 150ms ease,
              transform 150ms ease;
          }

          .alert-settings-button:hover {
            transform: translateY(-1px);
            background: rgba(52, 244, 181, 0.07);
            border-color: rgba(52, 244, 181, 0.16);
          }

          .alert-settings-dot {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            background: rgba(190, 198, 198, 0.42);
            box-shadow: 0 0 0 rgba(52, 244, 181, 0);
            transition:
              background 150ms ease,
              box-shadow 150ms ease;
          }

          .alert-settings-button.on .alert-settings-dot {
            background: #34f4b5;
            box-shadow:
              0 0 8px rgba(52, 244, 181, 0.85),
              0 0 18px rgba(52, 244, 181, 0.24);
          }

          .alert-settings-button.off .alert-settings-dot {
            background: rgba(190, 198, 198, 0.28);
            box-shadow: none;
          }

          .alert-settings-popover {
            position: absolute;
            top: 38px;
            right: -34px;
            width: 300px;
            padding: 14px;
            border: 1px solid rgba(255, 255, 255, 0.13);
            border-radius: 14px;
            background: rgba(5, 17, 18, 0.985);
            box-shadow:
              0 20px 44px rgba(0, 0, 0, 0.48),
              inset 0 1px 0 rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            color: #eef6f4;
          }

          .alert-settings-popover::before {
            content: "";
            position: absolute;
            top: -7px;
            right: 42px;
            width: 12px;
            height: 12px;
            border-left: 1px solid rgba(255, 255, 255, 0.13);
            border-top: 1px solid rgba(255, 255, 255, 0.13);
            background: rgba(5, 17, 18, 0.985);
            transform: rotate(45deg);
          }

          .alert-popover-heading {
            position: relative;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 12px;
            padding: 2px 2px 12px;
            border-bottom: 1px solid rgba(255, 255, 255, 0.075);
          }

          .alert-popover-heading > div {
            display: flex;
            flex-direction: column;
            gap: 3px;
          }

          .alert-popover-heading strong {
            font-size: 14px;
          }

          .alert-popover-heading span {
            color: rgba(225, 235, 234, 0.54);
            font-size: 11px;
            line-height: 1.35;
          }

          .alert-popover-close {
            width: 28px;
            height: 28px;
            border: 0;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.045);
            color: rgba(235, 242, 242, 0.68);
            font-size: 19px;
            line-height: 1;
            cursor: pointer;
          }

          .alert-mode-list {
            display: flex;
            flex-direction: column;
            gap: 4px;
            padding: 10px 0;
          }

          .alert-mode-option {
            width: 100%;
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 9px 10px;
            border: 1px solid transparent;
            border-radius: 10px;
            background: transparent;
            color: rgba(239, 246, 245, 0.86);
            text-align: left;
            cursor: pointer;
            transition:
              background 140ms ease,
              border-color 140ms ease;
          }

          .alert-mode-option:hover:not(:disabled):not(.disabled-option) {
            background: rgba(255, 255, 255, 0.045);
            border-color: rgba(255, 255, 255, 0.06);
          }

          .alert-mode-option.selected {
            background: rgba(52, 244, 181, 0.075);
            border-color: rgba(52, 244, 181, 0.19);
          }

          .alert-radio {
            width: 16px;
            color: rgba(220, 230, 229, 0.46);
            font-size: 15px;
            flex: 0 0 auto;
          }

          .alert-mode-option.selected .alert-radio {
            color: #34f4b5;
          }

          .alert-option-copy {
            display: flex;
            flex: 1;
            min-width: 0;
            flex-direction: column;
            gap: 2px;
          }

          .alert-option-copy strong {
            font-size: 12px;
            font-weight: 750;
          }

          .alert-option-copy small {
            color: rgba(225, 235, 234, 0.46);
            font-size: 10px;
            line-height: 1.25;
          }

          .disabled-option {
            opacity: 0.42;
            cursor: default;
          }

          .alert-email-row {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
            padding: 12px 3px 3px;
            border-top: 1px solid rgba(255, 255, 255, 0.075);
          }

          .alert-email-row > div {
            display: flex;
            flex-direction: column;
            gap: 2px;
          }

          .alert-email-row strong {
            font-size: 12px;
          }

          .alert-email-row span {
            color: rgba(225, 235, 234, 0.46);
            font-size: 10px;
          }

          .alert-email-toggle {
            position: relative;
            width: 39px;
            height: 23px;
            padding: 0;
            border: 1px solid rgba(255, 255, 255, 0.12);
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.07);
            cursor: pointer;
            transition:
              background 150ms ease,
              border-color 150ms ease;
          }

          .alert-email-toggle > span {
            position: absolute;
            top: 3px;
            left: 3px;
            width: 15px;
            height: 15px;
            border-radius: 999px;
            background: rgba(238, 244, 243, 0.82);
            transition:
              left 150ms ease,
              background 150ms ease;
          }

          .alert-email-toggle.on {
            background: rgba(52, 244, 181, 0.2);
            border-color: rgba(52, 244, 181, 0.42);
          }

          .alert-email-toggle.on > span {
            left: 19px;
            background: #34f4b5;
          }

          .alert-email-toggle:disabled,
          .alert-mode-option:disabled {
            cursor: wait;
          }

          .alert-save-status,
          .alert-save-error {
            margin-top: 9px;
            padding: 8px 9px;
            border-radius: 8px;
            font-size: 10px;
            line-height: 1.35;
          }

          .alert-save-status {
            background: rgba(52, 244, 181, 0.07);
            color: rgba(126, 255, 211, 0.82);
          }

          .alert-save-error {
            background: rgba(255, 92, 92, 0.08);
            color: #ff9b9b;
          }

          .pretty-product-row::before {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 2px;
            background: linear-gradient(
              180deg,
              rgba(52, 244, 181, 0.9),
              rgba(52, 244, 181, 0.16)
            );
            opacity: 0.70;
            transition: opacity 160ms ease;
          }

          .pretty-product-row:hover {
            transform: translateY(-1px);
            border-color: rgba(52, 244, 181, 0.22);
            background:
              linear-gradient(
                100deg,
                rgba(20, 35, 36, 0.72) 0%,
                rgba(26, 35, 33, 0.62) 52%,
                rgba(64, 55, 30, 0.48) 100%
              );
            box-shadow:
              inset 0 1px 0 rgba(255, 255, 255, 0.04),
              0 10px 24px rgba(0, 0, 0, 0.18);
          }

          .pretty-product-row:hover::before {
            opacity: 1;
          }

          .pretty-product-row :global(.pretty-product-thumb) {
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow:
              0 4px 12px rgba(0, 0, 0, 0.2),
              inset 0 1px 0 rgba(255, 255, 255, 0.08);
          }

          .pretty-product-row :global(.pretty-product-metric) {
            position: relative;
          }

          .pretty-product-row :global(.pretty-product-metric)::after {
            content: "";
            position: absolute;
            right: -12px;
            top: 20%;
            width: 1px;
            height: 60%;
            background: rgba(255, 255, 255, 0.045);
          }

          .pretty-product-row :global(.pretty-product-actions) {
            padding-left: 2px;
            gap: 7px;
          }

          .pretty-product-row :global(.product-action-link) {
            padding-left: 10px;
            padding-right: 10px;
          }

          .pretty-product-row :global(.pretty-trash-button) {
            border-color: rgba(255, 92, 92, 0.26);
            color: rgba(255, 108, 108, 0.80);
            background: rgba(74, 13, 13, 0.14);
            border-radius: 9px;
            transition:
              color 150ms ease,
              background 150ms ease,
              border-color 150ms ease,
              transform 150ms ease,
              box-shadow 150ms ease;
          }

          .pretty-product-row :global(.pretty-trash-button):hover:not(:disabled) {
            color: #ff8f8f;
            background: rgba(255, 90, 90, 0.11);
            border-color: rgba(255, 110, 110, 0.42);
            box-shadow: 0 0 0 1px rgba(255, 110, 110, 0.08);
            transform: translateY(-1px);
          }

          .target-price-cell {
            min-width: 0;
          }

          .target-display-wrap {
            display: flex;
            align-items: center;
            gap: 9px;
          }

          .target-edit-button {
            width: 29px;
            height: 29px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid transparent;
            border-radius: 8px;
            background: transparent;
            color: rgba(235, 242, 242, 0.70);
            cursor: pointer;
            transition:
              color 150ms ease,
              background 150ms ease,
              border-color 150ms ease,
              transform 150ms ease;
          }

          .target-edit-button:hover {
            color: #34f4b5;
            background: rgba(52, 244, 181, 0.07);
            border-color: rgba(52, 244, 181, 0.18);
            transform: translateY(-1px);
          }

          .target-edit-wrap {
            display: flex;
            flex-direction: column;
            gap: 6px;
            width: 116px;
            min-width: 0;
          }

          .target-input-wrap {
            display: flex;
            align-items: center;
            width: 116px;
            height: 36px;
            border: 1px solid rgba(52, 244, 181, 0.58);
            border-radius: 9px;
            background: rgba(2, 12, 14, 0.88);
            overflow: hidden;
            box-shadow:
              0 0 0 1px rgba(52, 244, 181, 0.05),
              0 5px 16px rgba(0, 0, 0, 0.14);
          }

          .target-input-wrap > span {
            padding-left: 11px;
            color: #34f4b5;
            font-weight: 800;
          }

          .target-input-wrap input {
            width: 100%;
            min-width: 0;
            padding: 0 9px 0 5px;
            border: 0;
            outline: none;
            background: transparent;
            color: #ffffff;
            font: inherit;
            font-weight: 700;
          }

          .target-edit-actions {
            display: flex;
            gap: 7px;
          }

          .target-save-button,
          .target-cancel-button {
            flex: 1;
            min-height: 29px;
            padding: 0 7px;
            border-radius: 8px;
            font: inherit;
            font-size: 12px;
            font-weight: 750;
            cursor: pointer;
            transition:
              opacity 150ms ease,
              transform 150ms ease,
              background 150ms ease,
              border-color 150ms ease;
          }

          .target-save-button {
            border: 1px solid rgba(52, 244, 181, 0.50);
            background: #34f4b5;
            color: #04100d;
          }

          .target-save-button:hover:not(:disabled) {
            transform: translateY(-1px);
          }

          .target-cancel-button {
            border: 1px solid rgba(255, 255, 255, 0.10);
            background: rgba(255, 255, 255, 0.055);
            color: rgba(240, 245, 245, 0.80);
          }

          .target-cancel-button:hover:not(:disabled) {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
          }

          .target-save-button:disabled,
          .target-cancel-button:disabled {
            opacity: 0.55;
            cursor: wait;
          }

          .target-gap-cell {
            min-width: 0;
          }

          .target-gap-reached {
            color: #34f4b5;
          }

          .target-gap-above {
            color: #ff9c86;
          }

          .target-gap-neutral {
            color: rgba(231, 239, 239, 0.45);
          }

          .products-panel::after {
            content: "";
            display: block;
            height: 1px;
            background: linear-gradient(
              90deg,
              rgba(52, 244, 181, 0.32),
              rgba(255, 255, 255, 0.04) 45%,
              rgba(255, 255, 255, 0)
            );
          }

          @media (max-width: 1450px) {
            .pretty-product-row {
              grid-template-columns:
                62px
                minmax(175px, 1.4fr)
                82px
                82px
                78px
                108px
                82px
                20px
                minmax(292px, auto) !important;
              column-gap: 7px !important;
            }

            .pretty-product-row :global(.product-action-link) {
              padding-left: 8px;
              padding-right: 8px;
            }
          }

          @media (max-width: 1100px) {
            .pretty-products-list {
              padding-left: 8px;
              padding-right: 8px;
            }

            .pretty-product-row :global(.pretty-product-metric)::after {
              display: none;
            }
          }
        `}</style>

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
