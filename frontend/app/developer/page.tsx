"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../utils/supabase/client";

type DeveloperStatus = {
  name: string;
  email: string;
  role: string;
  productCount: number;
  backendOnline: boolean | null;
};

const API_BASE_URL = "http://127.0.0.1:8000";

function getDisplayName(user: any) {
  return (
    user?.user_metadata?.display_name ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "Developer"
  );
}

export default function DeveloperPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<DeveloperStatus | null>(null);
  const [supportedStores, setSupportedStores] = useState<string[]>([]);

  useEffect(() => {
    const supabase = createClient();

    async function loadDeveloperPage() {
      try {
        const {
          data: { user },
        } = await supabase.auth.getUser();

        if (!user) {
          router.replace("/login");
          return;
        }

        const { data: profile, error: profileError } = await supabase
          .from("profiles")
          .select("role, display_name")
          .eq("user_id", user.id)
          .maybeSingle();

        if (profileError || profile?.role !== "developer") {
          router.replace("/");
          return;
        }

        const { count } = await supabase
          .from("products")
          .select("*", { count: "exact", head: true });

        let backendOnline: boolean | null = null;

        try {
          const response = await fetch(`${API_BASE_URL}/`, {
            cache: "no-store",
          });
          backendOnline = response.ok;
        } catch {
          backendOnline = false;
        }

        try {
          const response = await fetch(
            `${API_BASE_URL}/compare/supported-stores`,
            { cache: "no-store" },
          );

          if (response.ok) {
            const result = await response.json();
            setSupportedStores(
              Array.isArray(result?.stores) ? result.stores : [],
            );
          } else {
            setSupportedStores([]);
          }
        } catch {
          setSupportedStores([]);
        }

        setStatus({
          name: profile.display_name || getDisplayName(user),
          email: user.email || "",
          role: profile.role,
          productCount: count ?? 0,
          backendOnline,
        });
      } finally {
        setLoading(false);
      }
    }

    void loadDeveloperPage();
  }, [router]);

  if (loading) {
    return (
      <section className="developer-page">
        <div className="glass-card developer-loading">Loading developer tools…</div>
      </section>
    );
  }

  if (!status) {
    return null;
  }

  return (
    <>
      <style jsx global>{`
        .developer-page {
          padding-bottom: 40px;
        }

        .developer-header {
          display: flex;
          align-items: flex-end;
          justify-content: space-between;
          gap: 20px;
          margin-bottom: 22px;
        }

        .developer-header h2 {
          margin: 4px 0 5px;
          font-size: 30px;
        }

        .developer-header p {
          margin: 0;
          color: rgba(235, 243, 242, 0.55);
        }

        .developer-badge {
          padding: 8px 11px;
          border-radius: 999px;
          border: 1px solid rgba(52, 238, 182, 0.2);
          background: rgba(52, 238, 182, 0.08);
          color: var(--mint);
          font-size: 10px;
          font-weight: 900;
          letter-spacing: 0.08em;
          text-transform: uppercase;
        }

        .developer-stat-grid {
          display: grid;
          grid-template-columns: repeat(4, minmax(0, 1fr));
          gap: 14px;
          margin-bottom: 18px;
        }

        .developer-stat-card {
          padding: 18px;
          min-height: 118px;
        }

        .developer-stat-label {
          color: rgba(235, 243, 242, 0.43);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.07em;
          text-transform: uppercase;
        }

        .developer-stat-value {
          display: block;
          margin-top: 10px;
          font-size: 22px;
          font-weight: 900;
          color: rgba(248, 251, 250, 0.96);
        }

        .developer-stat-note {
          display: block;
          margin-top: 7px;
          color: rgba(235, 243, 242, 0.45);
          font-size: 11px;
        }

        .developer-status-dot {
          display: inline-block;
          width: 8px;
          height: 8px;
          margin-right: 7px;
          border-radius: 999px;
          background: var(--mint);
          box-shadow: 0 0 12px rgba(52, 238, 182, 0.5);
        }

        .developer-status-dot.offline {
          background: #ff8f73;
          box-shadow: none;
        }

        .developer-grid {
          display: grid;
          grid-template-columns: minmax(0, 1.2fr) minmax(320px, 0.8fr);
          gap: 18px;
        }

        .developer-card {
          padding: 20px;
        }

        .developer-card h3 {
          margin: 0 0 5px;
          font-size: 17px;
        }

        .developer-card > p {
          margin: 0 0 18px;
          color: rgba(235, 243, 242, 0.48);
          font-size: 12px;
          line-height: 1.5;
        }

        .developer-info-list {
          display: grid;
        }

        .developer-info-row {
          display: grid;
          grid-template-columns: 155px minmax(0, 1fr);
          gap: 18px;
          padding: 14px 0;
          border-bottom: 1px solid rgba(255, 255, 255, 0.055);
        }

        .developer-info-row:last-child {
          border-bottom: 0;
        }

        .developer-info-label {
          color: rgba(235, 243, 242, 0.4);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.06em;
          text-transform: uppercase;
        }

        .developer-info-value {
          color: rgba(248, 251, 250, 0.92);
          font-size: 12px;
          font-weight: 700;
        }

        .developer-store-list {
          display: grid;
          gap: 9px;
        }

        .developer-store-row {
          min-height: 43px;
          padding: 0 12px;
          display: flex;
          align-items: center;
          justify-content: space-between;
          border-radius: 10px;
          border: 1px solid rgba(255, 255, 255, 0.06);
          background: rgba(255, 255, 255, 0.025);
          font-size: 12px;
          font-weight: 700;
        }

        .developer-store-status {
          color: var(--mint);
          font-size: 10px;
          font-weight: 900;
          text-transform: uppercase;
        }

        .developer-coming-next {
          margin-top: 18px;
          padding: 16px;
          border-radius: 12px;
          border: 1px dashed rgba(52, 238, 182, 0.18);
          background: rgba(52, 238, 182, 0.035);
        }

        .developer-coming-next strong {
          display: block;
          margin-bottom: 5px;
          color: var(--mint);
          font-size: 12px;
        }

        .developer-coming-next span {
          color: rgba(235, 243, 242, 0.52);
          font-size: 11px;
          line-height: 1.5;
        }

        .developer-loading {
          padding: 24px;
          color: rgba(235, 243, 242, 0.55);
        }

        @media (max-width: 1100px) {
          .developer-stat-grid {
            grid-template-columns: repeat(2, minmax(0, 1fr));
          }

          .developer-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <section className="developer-page">
        <header className="developer-header">
          <div>
            <span className="eyebrow">ADMIN & DIAGNOSTICS</span>
            <h2>Developer</h2>
            <p>Private tools and system information for Wishlist developers.</p>
          </div>

          <span className="developer-badge">Developer Access</span>
        </header>

        <div className="developer-stat-grid">
          <section className="glass-card developer-stat-card">
            <span className="developer-stat-label">Role</span>
            <strong className="developer-stat-value">Developer</strong>
            <span className="developer-stat-note">Privileged account</span>
          </section>

          <section className="glass-card developer-stat-card">
            <span className="developer-stat-label">My Products</span>
            <strong className="developer-stat-value">{status.productCount}</strong>
            <span className="developer-stat-note">Owned by this account</span>
          </section>

          <section className="glass-card developer-stat-card">
            <span className="developer-stat-label">Backend</span>
            <strong className="developer-stat-value">
              <span
                className={`developer-status-dot ${
                  status.backendOnline ? "" : "offline"
                }`}
              />
              {status.backendOnline ? "Online" : "Offline"}
            </strong>
            <span className="developer-stat-note">FastAPI price checker</span>
          </section>

          <section className="glass-card developer-stat-card">
            <span className="developer-stat-label">Supported Stores</span>
            <strong className="developer-stat-value">
              {supportedStores.length}
            </strong>
            <span className="developer-stat-note">Supported retailers</span>
          </section>
        </div>

        <div className="developer-grid">
          <section className="glass-card developer-card">
            <h3>Developer account</h3>
            <p>
              This is separate from your normal Wishlist data. Your Dashboard
              still behaves like an ordinary user account.
            </p>

            <div className="developer-info-list">
              <div className="developer-info-row">
                <span className="developer-info-label">Display name</span>
                <span className="developer-info-value">{status.name}</span>
              </div>

              <div className="developer-info-row">
                <span className="developer-info-label">Email</span>
                <span className="developer-info-value">{status.email}</span>
              </div>

              <div className="developer-info-row">
                <span className="developer-info-label">Profile role</span>
                <span className="developer-info-value">{status.role}</span>
              </div>

              <div className="developer-info-row">
                <span className="developer-info-label">Access model</span>
                <span className="developer-info-value">
                  Developer tools only — normal product data stays user-scoped
                </span>
              </div>
            </div>

            <div className="developer-coming-next">
              <strong>Next developer tools</strong>
              <span>
                Scraper diagnostics, forced price checks, retailer health,
                beta-user management and system logs can live here as we add
                them.
              </span>
            </div>
          </section>

          <section className="glass-card developer-card">
            <h3>Retailer status</h3>
            <p>Stores currently exposed in the Wishlist beta sidebar.</p>

            <div className="developer-store-list">
              {supportedStores.map((store) => (
                <div className="developer-store-row" key={store}>
                  <span>{store}</span>
                  <span className="developer-store-status">Enabled</span>
                </div>
              ))}
            </div>
          </section>
        </div>
      </section>
    </>
  );
}
