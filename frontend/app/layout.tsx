import type { Metadata } from "next";
import "./globals.css";

import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

export const metadata: Metadata = {
  title: "Wishlist",
  description: "Track smarter. Shop better. Save more.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>
        <main className="site-shell">
          <div className="background-layer" aria-hidden="true" />
          <div className="background-shade" aria-hidden="true" />

          <Sidebar />

          <section className="dashboard">
            <TopBar />
            {children}
          </section>
        </main>
      </body>
    </html>
  );
}
