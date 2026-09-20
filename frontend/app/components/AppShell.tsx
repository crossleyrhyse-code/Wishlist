"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import { createClient } from "../../utils/supabase/client";
import Sidebar from "./Sidebar";
import TopBar from "./TopBar";

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [authChecked, setAuthChecked] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  useEffect(() => {
    const supabase = createClient();

    async function checkAuth() {
      const { data: { user } } = await supabase.auth.getUser();
      setIsLoggedIn(Boolean(user));
      setAuthChecked(true);
    }

    void checkAuth();

    const { data: { subscription } } = supabase.auth.onAuthStateChange((_event, session) => {
      setIsLoggedIn(Boolean(session?.user));
      setAuthChecked(true);
    });

    return () => subscription.unsubscribe();
  }, []);

  const isAuthPage = pathname === "/login" || pathname === "/signup";
  const isPublicHome = pathname === "/" && authChecked && !isLoggedIn;
  const usePublicShell = isAuthPage || isPublicHome;

  if (!authChecked && pathname === "/") {
    return <main className="public-shell"><div className="public-auth-loading" /></main>;
  }

  if (usePublicShell) {
    return <main className="public-shell">{children}</main>;
  }

  return (
    <main className="site-shell">
      <div className="background-layer" aria-hidden="true" />
      <div className="background-shade" aria-hidden="true" />
      <Sidebar />
      <section className="dashboard">
        <TopBar />
        {children}
      </section>
    </main>
  );
}
