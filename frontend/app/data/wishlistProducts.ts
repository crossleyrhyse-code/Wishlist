"use client";

import { createClient } from "../../utils/supabase/client";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000";

export type WishlistProductRecord = {
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
  priceHistory: { checkedAt: string; price: number }[];
  alertSettings?: {
    mode:
      | "TARGET_REACHED"
      | "PRICE_DROP"
      | "PRICE_CHANGE"
      | "DAILY_DIGEST"
      | "WEEKLY_DIGEST"
      | "OFF";
    emailEnabled: boolean;
  };
  notificationPending?: boolean;
  notificationTriggeredAt?: string | null;
  notificationReason?: string | null;
  notes?: string | null;
};

function numberOrNull(value: unknown): number | null {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function mapProductRow(row: Record<string, any>): WishlistProductRecord {
  return {
    id: row.id,
    name: row.name ?? row.display_name ?? "",
    displayName: row.display_name ?? row.name ?? "",
    store: row.store ?? "",
    category: row.category ?? "Other",
    url: row.url ?? "",
    targetPrice: numberOrNull(row.target_price),
    imageUrl: row.image_url ?? null,
    currentPrice: numberOrNull(row.current_price),
    addedPrice: numberOrNull(row.added_price),
    priceSelector: row.price_selector ?? null,
    source: row.source ?? "wishlist",
    addedOrder: Number(row.added_order ?? 0),
    lastChecked: row.last_checked ?? null,
    priceHistory: Array.isArray(row.price_history) ? row.price_history : [],
    alertSettings:
      row.alert_settings && typeof row.alert_settings === "object"
        ? row.alert_settings
        : {
            mode: "TARGET_REACHED",
            emailEnabled: true,
          },
    notificationPending: Boolean(row.notification_pending),
    notificationTriggeredAt: row.notification_triggered_at ?? null,
    notificationReason: row.notification_reason ?? null,
    notes: row.notes ?? null,
  };
}

async function requireUser() {
  const supabase = createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    throw new Error("You need to be logged in to use your Wishlist.");
  }

  return { supabase, user };
}

export async function loadWishlistProducts(): Promise<WishlistProductRecord[]> {
  const { supabase } = await requireUser();

  const { data, error } = await supabase
    .from("products")
    .select("*")
    .order("added_order", { ascending: false });

  if (error) {
    throw new Error(error.message || "Could not load Wishlist products.");
  }

  return (data ?? []).map((row) => mapProductRow(row));
}

export async function addWishlistProduct(input: {
  url: string;
  displayName: string;
  store: string;
  category: string;
  currentPrice: number;
  imageUrl: string | null;
  targetPrice: number | null;
  notes?: string | null;
}): Promise<WishlistProductRecord> {
  const { supabase, user } = await requireUser();

  const { data: duplicate, error: duplicateError } = await supabase
    .from("products")
    .select("id")
    .eq("url", input.url)
    .maybeSingle();

  if (duplicateError) {
    throw new Error(duplicateError.message);
  }

  if (duplicate) {
    throw new Error("This product is already in your Wishlist.");
  }

  const checkedAt = new Date().toISOString();

  const { data, error } = await supabase
    .from("products")
    .insert({
      user_id: user.id,
      name: input.displayName,
      display_name: input.displayName,
      store: input.store,
      category: input.category,
      url: input.url,
      target_price: input.targetPrice,
      image_url: input.imageUrl,
      current_price: input.currentPrice,
      added_price: input.currentPrice,
      price_selector: null,
      source: "wishlist",
      added_order: Date.now(),
      last_checked: checkedAt,
      price_history: [
        {
          checkedAt,
          price: input.currentPrice,
        },
      ],
      alert_settings: {
        mode: "TARGET_REACHED",
        emailEnabled: true,
      },
      notes: input.notes ?? null,
    })
    .select("*")
    .single();

  if (error) {
    throw new Error(error.message || "Could not add this product.");
  }

  return mapProductRow(data);
}

export async function updateWishlistProduct(
  productId: string,
  patch: {
    targetPrice?: number | null;
    alertSettings?: WishlistProductRecord["alertSettings"];
  },
): Promise<WishlistProductRecord> {
  const { supabase } = await requireUser();

  const dbPatch: Record<string, unknown> = {};

  if ("targetPrice" in patch) {
    dbPatch.target_price = patch.targetPrice ?? null;
  }

  if ("alertSettings" in patch) {
    dbPatch.alert_settings = patch.alertSettings ?? {
      mode: "TARGET_REACHED",
      emailEnabled: true,
    };
  }

  const { data, error } = await supabase
    .from("products")
    .update(dbPatch)
    .eq("id", productId)
    .select("*")
    .single();

  if (error) {
    throw new Error(error.message || "Could not update this product.");
  }

  return mapProductRow(data);
}

export async function deleteWishlistProduct(productId: string): Promise<void> {
  const { supabase } = await requireUser();

  const { error } = await supabase.from("products").delete().eq("id", productId);

  if (error) {
    throw new Error(error.message || "Could not remove this product.");
  }
}

export async function checkWishlistProductPrice(
  product: WishlistProductRecord,
): Promise<WishlistProductRecord> {
  const response = await fetch(`${API_BASE_URL}/check-price`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      url: product.url,
    }),
  });

  const result = await response.json();

  if (!response.ok) {
    throw new Error(result.detail || "Price check failed.");
  }

  const newPrice = Number(result.price);

  if (!Number.isFinite(newPrice)) {
    throw new Error("Wishlist received an invalid price from the checker.");
  }

  const { supabase } = await requireUser();
  const checkedAt = new Date().toISOString();
  const history = [
    ...(product.priceHistory ?? []),
    {
      checkedAt,
      price: newPrice,
    },
  ];

  const { data, error } = await supabase
    .from("products")
    .update({
      current_price: newPrice,
      last_checked: checkedAt,
      price_history: history,
    })
    .eq("id", product.id)
    .select("*")
    .single();

  if (error) {
    throw new Error(error.message || "Could not save the new product price.");
  }

  return mapProductRow(data);
}
