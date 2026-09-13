"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
type DigestContent = "CHANGED_ONLY" | "ALL_TRACKED";

export default function SettingsPage() {
  const [digestContent, setDigestContent] =
    useState<DigestContent>("CHANGED_ONLY");

  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const stored = window.localStorage.getItem(
      "wishlistDigestContent",
    );

    if (
      stored === "ALL_TRACKED" ||
      stored === "CHANGED_ONLY"
    ) {
      setDigestContent(stored);
    }
  }, []);

  function chooseDigestContent(value: DigestContent) {
    setDigestContent(value);

    window.localStorage.setItem(
      "wishlistDigestContent",
      value,
    );

    setSaved(true);

    window.setTimeout(() => {
      setSaved(false);
    }, 1800);
  }

  return (
    <>
      <style jsx global>{`
        .settings-page {
          padding-bottom: 40px;
        }

        .settings-page-header {
          margin-bottom: 24px;
        }

        .settings-page-header h2 {
          margin: 4px 0 5px;
          font-size: 30px;
        }

        .settings-page-header p {
          margin: 0;
          color: rgba(235, 243, 242, 0.55);
        }

        .settings-page-grid {
          display: grid;
          grid-template-columns: minmax(0, 1fr) 340px;
          gap: 20px;
        }

        .settings-main-card,
        .settings-info-card {
          padding: 22px;
        }

        .settings-card-title {
          display: flex;
          align-items: flex-start;
          gap: 14px;
          margin-bottom: 20px;
        }

        .settings-card-icon {
          width: 42px;
          height: 42px;
          border-radius: 12px;
          background: rgba(52, 238, 182, 0.1);
          border: 1px solid rgba(52, 238, 182, 0.16);
          color: var(--mint);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 18px;
          flex: 0 0 auto;
        }

        .settings-card-title h3 {
          margin: 1px 0 4px;
        }

        .settings-card-title p {
          margin: 0;
          color: rgba(235, 243, 242, 0.52);
          font-size: 12px;
          line-height: 1.5;
        }

        .settings-option-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .settings-option {
          width: 100%;
          display: grid;
          grid-template-columns: 24px minmax(0, 1fr) auto;
          gap: 12px;
          align-items: center;
          padding: 16px;
          text-align: left;
          border-radius: 12px;
          border: 1px solid rgba(255, 255, 255, 0.07);
          background: rgba(5, 15, 17, 0.45);
          color: inherit;
          cursor: pointer;
          transition:
            border-color 150ms ease,
            background 150ms ease;
        }

        .settings-option:hover,
        .settings-option.selected {
          border-color: rgba(52, 238, 182, 0.26);
          background: rgba(52, 238, 182, 0.055);
        }

        .settings-option-radio {
          color: var(--mint);
          font-size: 17px;
        }

        .settings-option-copy strong {
          display: block;
          margin-bottom: 4px;
        }

        .settings-option-copy small {
          display: block;
          color: rgba(235, 243, 242, 0.5);
          line-height: 1.45;
        }

        .settings-recommended {
          color: var(--mint);
          font-size: 10px;
          letter-spacing: 0.05em;
          text-transform: uppercase;
        }

        .settings-note {
          display: flex;
          gap: 11px;
          margin-top: 18px;
          padding: 14px;
          border-radius: 11px;
          background: rgba(255, 255, 255, 0.025);
          border: 1px solid rgba(255, 255, 255, 0.05);
          color: rgba(235, 243, 242, 0.55);
          font-size: 12px;
          line-height: 1.5;
        }

        .settings-note > span {
          color: var(--mint);
          font-weight: 800;
        }

        .settings-note p {
          margin: 0;
        }

        .settings-note a {
          color: var(--mint);
        }

        .settings-saved-message {
          margin-top: 13px;
          color: var(--mint);
          font-size: 12px;
          font-weight: 700;
        }

        .settings-info-card h3 {
          margin: 5px 0 10px;
        }

        .settings-info-card p {
          color: rgba(235, 243, 242, 0.52);
          line-height: 1.6;
          font-size: 13px;
        }

        .settings-info-card .secondary-page-button {
          margin-top: 12px;
          display: inline-flex;
        }

        @media (max-width: 1050px) {
          .settings-page-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
<section className="settings-page">
          <header className="settings-page-header">
            <span className="eyebrow">PREFERENCES</span>
            <h2>Settings</h2>
            <p>Choose how Wishlist works for you.</p>
          </header>

          <div className="settings-page-grid">
            <section className="glass-card settings-main-card">
              <div className="settings-card-title">
                <div className="settings-card-icon">✉</div>

                <div>
                  <h3>Email summaries</h3>
                  <p>
                    Choose what Wishlist should include in future
                    daily or weekly summaries.
                  </p>
                </div>
              </div>

              <div className="settings-option-list">
                <button
                  type="button"
                  className={`settings-option ${
                    digestContent === "CHANGED_ONLY"
                      ? "selected"
                      : ""
                  }`}
                  onClick={() =>
                    chooseDigestContent("CHANGED_ONLY")
                  }
                >
                  <span className="settings-option-radio">
                    {digestContent === "CHANGED_ONLY"
                      ? "●"
                      : "○"}
                  </span>

                  <span className="settings-option-copy">
                    <strong>Changed products only</strong>
                    <small>
                      Only include products whose price changed
                      during the summary period.
                    </small>
                  </span>

                  <b className="settings-recommended">
                    Recommended
                  </b>
                </button>

                <button
                  type="button"
                  className={`settings-option ${
                    digestContent === "ALL_TRACKED"
                      ? "selected"
                      : ""
                  }`}
                  onClick={() =>
                    chooseDigestContent("ALL_TRACKED")
                  }
                >
                  <span className="settings-option-radio">
                    {digestContent === "ALL_TRACKED"
                      ? "●"
                      : "○"}
                  </span>

                  <span className="settings-option-copy">
                    <strong>All tracked products</strong>
                    <small>
                      Include every tracked product, even if its
                      price has not changed.
                    </small>
                  </span>
                </button>
              </div>

              <div className="settings-note">
                <span>i</span>

                <p>
                  Individual product alert settings are still managed
                  from{" "}
                  <Link href="/products">My Products</Link>.
                </p>
              </div>

              {saved && (
                <div className="settings-saved-message">
                  ✓ Preference saved
                </div>
              )}
            </section>

            <section className="glass-card settings-info-card">
              <span className="eyebrow">PRODUCT ALERTS</span>

              <h3>Each product has its own alert</h3>

              <p>
                Use the alert control beside a product to choose
                whether Wishlist should watch its target price,
                price drops, price changes, or turn alerts off.
              </p>

              <Link
                href="/products"
                className="secondary-page-button"
              >
                Open My Products →
              </Link>
            </section>
          </div>
        </section>
</>
  );
}