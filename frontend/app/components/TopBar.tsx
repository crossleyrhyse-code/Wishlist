"use client";

import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import DynamicGreeting from "./DynamicGreeting";
import AccountMenu from "./AccountMenu";
import { loadWishlistProducts } from "../data/wishlistProducts";

type AlertMode =
  | "TARGET_REACHED"
  | "PRICE_DROP"
  | "PRICE_CHANGE"
  | "DAILY_DIGEST"
  | "WEEKLY_DIGEST"
  | "OFF";

type SearchProduct = {
  id: string;
  name: string;
  displayName: string;
  store: string;
  category: string;
  imageUrl: string | null;
  currentPrice: number | null;
  alertSettings?: {
    mode: AlertMode;
    emailEnabled: boolean;
  };
};

function money(value: number | null) {
  if (value === null) return "Not checked";

  return new Intl.NumberFormat("en-AU", {
    style: "currency",
    currency: "AUD",
  }).format(value);
}

export default function TopBar() {
  const [products, setProducts] = useState<SearchProduct[]>([]);
  const [search, setSearch] = useState("");
  const [searchOpen, setSearchOpen] = useState(false);
  const [searchError, setSearchError] = useState("");

  const searchWrapRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    async function loadProducts() {
      try {
        const result = (await loadWishlistProducts()) as SearchProduct[];
        setProducts(result);
        setSearchError("");
      } catch {
        setProducts([]);
        setSearchError("");
      }
    }

    loadProducts();
  }, []);

  useEffect(() => {
    function handleOutsideClick(event: MouseEvent) {
      if (
        searchWrapRef.current &&
        !searchWrapRef.current.contains(event.target as Node)
      ) {
        setSearchOpen(false);
      }
    }

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setSearchOpen(false);
      }

      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();

        const input = document.getElementById(
          "wishlist-global-search",
        ) as HTMLInputElement | null;

        input?.focus();
      }
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, []);

  const results = useMemo(() => {
    const terms = search
      .trim()
      .toLowerCase()
      .split(/\s+/)
      .filter(Boolean);

    if (!terms.length) {
      return [];
    }

    return products
      .filter((product) => {
        const searchableText = [
          product.displayName,
          product.name,
          product.store,
          product.category,
        ]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();

        return terms.every((term) => searchableText.includes(term));
      })
      .slice(0, 6);
  }, [products, search]);

  const activeAlertCount = useMemo(
    () =>
      products.filter(
        (product) =>
          (product.alertSettings?.mode ?? "TARGET_REACHED") !== "OFF",
      ).length,
    [products],
  );

  const hasSearch = search.trim().length > 0;

  return (
    <>
      <style jsx global>{`
        .wishlist-topbar-search {
          position: relative;
          flex: 1;
          min-width: 0;
        }

        .wishlist-topbar-search .search-box {
          width: 100%;
        }

        .global-search-results {
          position: absolute;
          top: calc(100% + 9px);
          left: 0;
          right: 0;
          z-index: 200;
          overflow: hidden;
          border-radius: 14px;
          border: 1px solid rgba(255, 255, 255, 0.1);
          background: rgba(7, 17, 19, 0.97);
          box-shadow: 0 20px 45px rgba(0, 0, 0, 0.42);
          backdrop-filter: blur(22px);
          -webkit-backdrop-filter: blur(22px);
        }

        .global-search-result {
          display: grid;
          grid-template-columns: 48px minmax(0, 1fr) auto;
          align-items: center;
          gap: 12px;
          min-height: 66px;
          padding: 9px 12px;
          color: inherit;
          text-decoration: none;
          border-bottom: 1px solid rgba(255, 255, 255, 0.055);
          transition:
            background 140ms ease,
            border-color 140ms ease;
        }

        .global-search-result:last-child {
          border-bottom: 0;
        }

        .global-search-result:hover {
          background: rgba(52, 238, 182, 0.065);
        }

        .global-search-image {
          width: 46px;
          height: 46px;
          display: flex;
          align-items: center;
          justify-content: center;
          overflow: hidden;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.07);
          background: rgba(255, 255, 255, 0.035);
        }

        .global-search-image img {
          width: 100%;
          height: 100%;
          object-fit: contain;
        }

        .global-search-copy {
          min-width: 0;
        }

        .global-search-copy strong {
          display: block;
          overflow: hidden;
          margin-bottom: 3px;
          color: rgba(248, 251, 250, 0.96);
          font-size: 12px;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .global-search-copy span {
          display: block;
          overflow: hidden;
          color: rgba(235, 243, 242, 0.48);
          font-size: 10px;
          font-weight: 700;
          white-space: nowrap;
          text-overflow: ellipsis;
        }

        .global-search-price {
          color: var(--mint);
          font-size: 12px;
          font-weight: 800;
          white-space: nowrap;
        }

        .global-search-empty {
          padding: 24px 18px;
          color: rgba(235, 243, 242, 0.5);
          text-align: center;
          font-size: 12px;
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
          z-index: 2;
        }

        .account-menu-trigger {
          display: flex;
          align-items: center;
          gap: 7px;
          border: 0;
          background: transparent;
          color: inherit;
          cursor: pointer;
          padding: 0;
        }

        @media (max-width: 900px) {
          .global-search-result {
            grid-template-columns: 42px minmax(0, 1fr);
          }

          .global-search-price {
            display: none;
          }
        }
      `}</style>

      <header className="dashboard-header">
        <DynamicGreeting />

        <div
          className="wishlist-topbar-search"
          ref={searchWrapRef}
        >
          <label className="search-box">
            <span className="search-icon">⌕</span>

            <input
              id="wishlist-global-search"
              type="search"
              placeholder="Search your products, brands or stores..."
              value={search}
              onChange={(event) => {
                setSearch(event.target.value);
                setSearchOpen(true);
              }}
              onFocus={() => {
                if (search.trim()) {
                  setSearchOpen(true);
                }
              }}
              autoComplete="off"
            />

            <kbd>Ctrl + K</kbd>
          </label>

          {searchOpen && hasSearch && (
            <div className="global-search-results">
              {searchError ? (
                <div className="global-search-empty">
                  {searchError}
                </div>
              ) : results.length === 0 ? (
                <div className="global-search-empty">
                  No matching products
                </div>
              ) : (
                results.map((product) => (
                  <Link
                    key={product.id}
                    href="/products"
                    className="global-search-result"
                    onClick={() => setSearchOpen(false)}
                  >
                    <div className="global-search-image">
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

                    <div className="global-search-copy">
                      <strong>{product.displayName}</strong>

                      <span>
                        {product.store}
                        {product.category
                          ? ` · ${product.category}`
                          : ""}
                      </span>
                    </div>

                    <span className="global-search-price">
                      {money(product.currentPrice)}
                    </span>
                  </Link>
                ))
              )}
            </div>
          )}
        </div>

        <div className="header-actions">
          <Link
            href="/alerts"
            className="notification-button"
            aria-label={`${activeAlertCount} active alerts`}
            title="Alerts"
          >
            <svg
              className="notification-bell"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9Z"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              <path
                d="M10 21h4"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
              />
            </svg>

            {activeAlertCount > 0 && (
              <span className="notification-badge">
                {activeAlertCount}
              </span>
            )}
          </Link>

          <AccountMenu />
        </div>
      </header>
    </>
  );
}