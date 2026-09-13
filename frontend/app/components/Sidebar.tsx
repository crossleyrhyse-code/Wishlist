"use client";

import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { createClient } from "../../utils/supabase/client";

const navItems = [
  ["⌂", "Dashboard", "/"],
  ["▣", "My Products", "/products"],
  ["＋", "Add Product", "/products/add"],
  ["⌕", "Price Comparison", "/compare"],
  ["⌁", "Price History", "/history"],
  ["♢", "Alerts", "/alerts"],
  ["⚙", "Settings", "/settings"],
] as const;

const developerNavItem = ["⚒", "Developer", "/developer"] as const;

type SupportedStore = {
  name: string;
  icon: string;
};

const API_BASE_URL = "http://127.0.0.1:8000";

function getStoreIcon(name: string) {
  if (name === "4WD Supacentre") return "4";
  return name.slice(0, 1).toUpperCase();
}

function isActive(pathname: string, href: string) {
  if (href === "/") {
    return pathname === "/";
  }

  if (href === "/products") {
    return pathname === "/products";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

export default function Sidebar() {
  const pathname = usePathname();
  const [isDeveloper, setIsDeveloper] = useState(false);
  const [supportedStores, setSupportedStores] = useState<SupportedStore[]>([]);

  useEffect(() => {
    const supabase = createClient();

    async function loadRole() {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        setIsDeveloper(false);
        return;
      }

      const { data, error } = await supabase
        .from("profiles")
        .select("role")
        .eq("user_id", user.id)
        .maybeSingle();

      if (error) {
        setIsDeveloper(false);
        return;
      }

      setIsDeveloper(data?.role === "developer");
    }

    async function loadSupportedStores() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/compare/supported-stores`,
          { cache: "no-store" },
        );

        if (!response.ok) {
          throw new Error("Could not load supported stores.");
        }

        const result = await response.json();
        const stores = Array.isArray(result?.stores) ? result.stores : [];

        setSupportedStores(
          stores.map((name: string) => ({
            name,
            icon: getStoreIcon(name),
          })),
        );
      } catch {
        setSupportedStores([]);
      }
    }

    void loadRole();
    void loadSupportedStores();

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange(() => {
      void loadRole();
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-logo-wrap">
          <Image
            src="/assets/wishlist-logo.png"
            alt="Wishlist"
            width={64}
            height={64}
            priority
            className="brand-logo"
          />
        </div>

        <div>
          <h1>Wishlist</h1>
        </div>
      </div>

      <nav className="primary-nav">
        {navItems.map(([icon, label, href]) => (
          <Link
            key={label}
            href={href}
            className={`nav-item ${isActive(pathname, href) ? "active" : ""}`}
          >
            <span className="nav-icon">{icon}</span>
            <span>{label}</span>
          </Link>
        ))}

        {isDeveloper && (
          <Link
            href={developerNavItem[2]}
            className={`nav-item ${
              isActive(pathname, developerNavItem[2]) ? "active" : ""
            }`}
          >
            <span className="nav-icon">{developerNavItem[0]}</span>
            <span>{developerNavItem[1]}</span>
          </Link>
        )}
      </nav>

      <div className="sidebar-divider" />
      <p className="sidebar-heading">SUPPORTED STORES</p>

      <nav className="category-nav">
        {supportedStores.map((store) => (
          <div
            key={store.name}
            className="nav-item category-item supported-store-item"
          >
            <span className="nav-icon">{store.icon}</span>
            <span>{store.name}</span>
          </div>
        ))}
      </nav>

      <div className="sidebar-spacer" />

      <button className="theme-switch" type="button">
        <span className="theme-toggle">
          <span className="theme-sun">☀</span>
          <span className="theme-knob" />
        </span>

        <span>Dark Mode</span>
        <span className="chevron">›</span>
      </button>
    </aside>
  );
}
