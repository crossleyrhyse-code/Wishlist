"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { createClient } from "../../utils/supabase/client";

function getName(user: any) {
  return (
    user?.user_metadata?.display_name ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "Wishlist User"
  );
}

function getInitials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export default function AccountPage() {
  const [name, setName] = useState("Loading...");
  const [email, setEmail] = useState("");
  const [avatar, setAvatar] = useState("...");
  const [createdAt, setCreatedAt] = useState("");

  useEffect(() => {
    const supabase = createClient();

    const applyUser = (user: any) => {
      if (!user) return;
      const nextName = getName(user);
      setName(nextName);
      setEmail(user.email || "");
      setAvatar(getInitials(nextName));
      setCreatedAt(
        user.created_at
          ? new Date(user.created_at).toLocaleDateString(undefined, {
              day: "numeric",
              month: "long",
              year: "numeric",
            })
          : "—"
      );
    };

    supabase.auth.getUser().then(({ data }) => applyUser(data.user));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session?.user) applyUser(session.user);
    });

    return () => subscription.unsubscribe();
  }, []);

  return (
    <>
      <style jsx global>{`
        .account-page { padding-bottom:40px; }
        .account-page-header { margin-bottom:24px; }
        .account-page-header h2 { margin:4px 0 5px; font-size:30px; }
        .account-page-header p { margin:0; color:rgba(235,243,242,.55); }
        .account-page-grid {
          display:grid; grid-template-columns:330px minmax(0,1fr); gap:20px; align-items:start;
        }
        .account-profile-card,.account-details-card { padding:22px; }
        .account-profile-card { display:flex; flex-direction:column; align-items:center; text-align:center; }
        .account-profile-avatar {
          width:86px; height:86px; border-radius:999px; display:flex; align-items:center;
          justify-content:center; margin-bottom:14px; background:var(--mint); color:#07110f;
          font-size:24px; font-weight:900; letter-spacing:.05em;
          box-shadow:0 0 28px rgba(52,238,182,.14);
        }
        .account-profile-card h3 { margin:0 0 4px; font-size:20px; }
        .account-profile-email { margin:0; color:rgba(235,243,242,.48); font-size:12px; }
        .account-beta-badge {
          margin-top:15px; padding:7px 10px; border-radius:999px;
          border:1px solid rgba(52,238,182,.16); background:rgba(52,238,182,.07);
          color:var(--mint); font-size:9px; font-weight:900; letter-spacing:.08em; text-transform:uppercase;
        }
        .account-profile-divider { width:100%; height:1px; margin:20px 0; background:rgba(255,255,255,.06); }
        .account-profile-actions { width:100%; display:grid; gap:9px; }
        .account-profile-actions a {
          min-height:42px; border-radius:10px; display:flex; align-items:center; justify-content:center;
          text-decoration:none; font-size:12px; font-weight:800;
        }
        .account-primary-action { background:var(--mint); color:#07110f; }
        .account-secondary-action {
          border:1px solid rgba(255,255,255,.08); background:rgba(255,255,255,.03);
          color:rgba(245,249,248,.9);
        }
        .account-details-heading {
          display:flex; justify-content:space-between; gap:20px; align-items:center;
          padding-bottom:16px; border-bottom:1px solid rgba(255,255,255,.06);
        }
        .account-details-heading h3 { margin:0 0 4px; }
        .account-details-heading p { margin:0; color:rgba(235,243,242,.48); font-size:12px; }
        .account-detail-list { display:grid; margin-top:4px; }
        .account-detail-row {
          display:grid; grid-template-columns:160px minmax(0,1fr); gap:20px;
          padding:17px 0; border-bottom:1px solid rgba(255,255,255,.055);
        }
        .account-detail-row:last-child { border-bottom:0; }
        .account-detail-label {
          color:rgba(235,243,242,.42); font-size:10px; font-weight:800;
          letter-spacing:.07em; text-transform:uppercase;
        }
        .account-detail-value { color:rgba(248,251,250,.93); font-size:13px; font-weight:700; }
        .account-coming-soon {
          margin-top:20px; padding:14px; border-radius:11px;
          border:1px solid rgba(255,255,255,.055); background:rgba(255,255,255,.025);
          color:rgba(235,243,242,.5); font-size:12px; line-height:1.5;
        }
        .account-coming-soon strong { color:rgba(248,251,250,.9); }
        @media (max-width:980px) {
          .account-page-grid { grid-template-columns:1fr; }
          .account-detail-row { grid-template-columns:1fr; gap:5px; }
        }
      `}</style>

      <section className="account-page">
        <header className="account-page-header">
          <span className="eyebrow">YOUR PROFILE</span>
          <h2>My Account</h2>
          <p>Manage your Wishlist profile and account details.</p>
        </header>

        <div className="account-page-grid">
          <section className="glass-card account-profile-card">
            <div className="account-profile-avatar">{avatar}</div>
            <h3>{name}</h3>
            <p className="account-profile-email">{email}</p>
            <span className="account-beta-badge">Wishlist Beta</span>

            <div className="account-profile-divider" />

            <div className="account-profile-actions">
              <Link href="/settings" className="account-primary-action">Account Settings</Link>
              <Link href="/products" className="account-secondary-action">My Products</Link>
            </div>
          </section>

          <section className="glass-card account-details-card">
            <div className="account-details-heading">
              <div>
                <h3>Profile details</h3>
                <p>Your basic Wishlist account information.</p>
              </div>
            </div>

            <div className="account-detail-list">
              <div className="account-detail-row">
                <span className="account-detail-label">Name</span>
                <span className="account-detail-value">{name}</span>
              </div>
              <div className="account-detail-row">
                <span className="account-detail-label">Email</span>
                <span className="account-detail-value">{email || "—"}</span>
              </div>
              <div className="account-detail-row">
                <span className="account-detail-label">Account status</span>
                <span className="account-detail-value">Active</span>
              </div>
              <div className="account-detail-row">
                <span className="account-detail-label">Membership</span>
                <span className="account-detail-value">Free</span>
              </div>
              <div className="account-detail-row">
                <span className="account-detail-label">Joined</span>
                <span className="account-detail-value">{createdAt || "—"}</span>
              </div>
            </div>

            <div className="account-coming-soon">
              <strong>Wishlist Beta:</strong> your account and tracked products are now tied to your signed-in user.
            </div>
          </section>
        </div>
      </section>
    </>
  );
}
