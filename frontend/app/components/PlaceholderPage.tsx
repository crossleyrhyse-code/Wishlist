"use client";

import Link from "next/link";
import Sidebar from "./Sidebar";

type PlaceholderPageProps = {
  title: string;
  description: string;
};

export default function PlaceholderPage({
  title,
  description,
}: PlaceholderPageProps) {
  return (
    <main className="site-shell">
      <div className="background-layer" aria-hidden="true" />
      <div className="background-shade" aria-hidden="true" />

      <Sidebar />

      <section className="dashboard products-dashboard">
        <header className="products-header">
          <div>
            <span className="eyebrow">WISHLIST</span>
            <h2>{title}</h2>
            <p>{description}</p>
          </div>
        </header>

        <section
          className="glass-card"
          style={{
            margin: "0 32px 32px",
            padding: "32px",
            minHeight: "260px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
          }}
        >
          <div>
            <strong
              style={{
                display: "block",
                fontSize: "20px",
                marginBottom: "8px",
              }}
            >
              {title}
            </strong>

            <p
              style={{
                maxWidth: "560px",
                margin: "0 auto 18px",
                color: "rgba(235,243,242,0.58)",
              }}
            >
              {description}
            </p>

            <Link href="/" className="secondary-page-button">
              Back to Dashboard →
            </Link>
          </div>
        </section>
      </section>
    </main>
  );
}
