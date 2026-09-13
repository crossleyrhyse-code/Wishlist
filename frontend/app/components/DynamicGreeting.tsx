"use client";

import { useEffect, useMemo, useState } from "react";
import { quotes } from "../data/quotes";
import { createClient } from "../../utils/supabase/client";

function getGreeting(hour: number) {
  if (hour < 12) return "Good morning";
  if (hour < 17) return "Good afternoon";
  return "Good evening";
}

function getDailyQuoteIndex(date: Date, quoteCount: number) {
  if (quoteCount === 0) return 0;

  const dateKey =
    date.getFullYear() * 10000 +
    (date.getMonth() + 1) * 100 +
    date.getDate();

  return dateKey % quoteCount;
}

function getDisplayName(user: any) {
  const candidates = [
    user?.user_metadata?.display_name,
    user?.user_metadata?.full_name,
    user?.user_metadata?.name,
  ];

  for (const candidate of candidates) {
    if (typeof candidate === "string" && candidate.trim()) {
      return candidate.trim();
    }
  }

  const email =
    typeof user?.email === "string"
      ? user.email.trim()
      : "";

  if (email) {
    return email.split("@")[0];
  }

  return "there";
}

function getFirstName(user: any) {
  const displayName = getDisplayName(user);
  return displayName.split(/\s+/)[0] || "there";
}

export default function DynamicGreeting() {
  const [now, setNow] = useState<Date | null>(null);
  const [firstName, setFirstName] = useState("there");

  useEffect(() => {
    const supabase = createClient();

    const refreshUser = async () => {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      setFirstName(user ? getFirstName(user) : "there");
    };

    setNow(new Date());
    void refreshUser();

    const timer = window.setInterval(() => {
      setNow(new Date());
    }, 60_000);

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setFirstName(
        session?.user
          ? getFirstName(session.user)
          : "there",
      );
    });

    return () => {
      window.clearInterval(timer);
      subscription.unsubscribe();
    };
  }, []);

  const greeting = now
    ? getGreeting(now.getHours())
    : "Welcome back";

  const quote = useMemo(() => {
    if (!now || quotes.length === 0) {
      return "Shopping is easy. Paying less is the fun part.";
    }

    return quotes[getDailyQuoteIndex(now, quotes.length)];
  }, [now]);

  return (
    <div className="greeting">
      <h2>
        {greeting},{" "}
        <span>{firstName}!</span>
      </h2>

      <div className="daily-quote">
        <em>{quote}</em>
      </div>
    </div>
  );
}
