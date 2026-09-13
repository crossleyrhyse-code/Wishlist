"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { createClient } from "../../utils/supabase/client";

function userName(user: any) {
  return (
    user?.user_metadata?.display_name ||
    user?.user_metadata?.full_name ||
    user?.user_metadata?.name ||
    user?.email?.split("@")[0] ||
    "Account"
  );
}

function initials(name: string) {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}

export default function AccountMenu() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("Account");
  const [email, setEmail] = useState("");
  const [avatar, setAvatar] = useState("?");
  const [loggingOut, setLoggingOut] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const supabase = createClient();

    const applyUser = (user: any) => {
      if (!user) {
        setName("Account");
        setEmail("");
        setAvatar("?");
        return;
      }
      const nextName = userName(user);
      setName(nextName);
      setEmail(user.email || "");
      setAvatar(initials(nextName));
    };

    supabase.auth.getUser().then(({ data }) => applyUser(data.user));

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      applyUser(session?.user ?? null);
    });

    function handleOutsideClick(event: MouseEvent) {
      if (
        menuRef.current &&
        !menuRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", handleOutsideClick);
    document.addEventListener("keydown", handleEscape);

    return () => {
      subscription.unsubscribe();
      document.removeEventListener("mousedown", handleOutsideClick);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  async function handleLogout() {
    setLoggingOut(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    setOpen(false);
    router.replace("/login");
    router.refresh();
  }

  return (
    <>
      <style jsx global>{`
        .account-menu-wrap { position: relative; }
        .account-menu-trigger {
          display: flex; align-items: center; gap: 7px; padding: 0; border: 0;
          background: transparent; color: inherit; cursor: pointer;
        }
        .account-menu-trigger .avatar {
          display: flex; align-items: center; justify-content: center; line-height: 1;
        }
        .account-menu-trigger .account-chevron { transition: transform 150ms ease; }
        .account-menu-trigger.open .account-chevron { transform: rotate(180deg); }
        .account-dropdown {
          position: absolute; top: calc(100% + 10px); right: 0; z-index: 300;
          width: 260px; overflow: hidden; border-radius: 14px;
          border: 1px solid rgba(255,255,255,.1); background: rgba(7,17,19,.98);
          box-shadow: 0 22px 50px rgba(0,0,0,.42); backdrop-filter: blur(22px);
          -webkit-backdrop-filter: blur(22px);
        }
        .account-dropdown-profile { display:flex; align-items:center; gap:12px; padding:16px; }
        .account-dropdown-avatar {
          width:44px; height:44px; border-radius:999px; display:flex; align-items:center;
          justify-content:center; flex:0 0 auto; background:var(--mint); color:#07110f;
          font-size:13px; font-weight:900; letter-spacing:.04em;
        }
        .account-dropdown-copy { min-width:0; }
        .account-dropdown-copy strong,.account-dropdown-copy span {
          display:block; overflow:hidden; white-space:nowrap; text-overflow:ellipsis;
        }
        .account-dropdown-copy strong { color:rgba(248,251,250,.96); font-size:13px; }
        .account-dropdown-copy span { margin-top:3px; color:rgba(235,243,242,.46); font-size:10px; }
        .account-dropdown-divider { height:1px; background:rgba(255,255,255,.06); }
        .account-dropdown-nav { padding:7px; }
        .account-dropdown-link {
          display:flex; align-items:center; gap:11px; min-height:42px; padding:0 11px;
          border-radius:10px; color:rgba(242,248,247,.86); text-decoration:none;
          font-size:12px; font-weight:700; transition:background 140ms ease;
        }
        .account-dropdown-link:hover { background:rgba(52,238,182,.07); }
        .account-dropdown-icon { width:19px; text-align:center; color:var(--mint); }
        .account-dropdown-logout {
          width:calc(100% - 14px); margin:7px; min-height:42px; padding:0 11px;
          border:0; border-radius:10px; display:flex; align-items:center; gap:11px;
          background:transparent; color:#ff8f73; font:inherit; font-size:12px;
          font-weight:700; cursor:pointer; text-align:left;
        }
        .account-dropdown-logout:hover { background:rgba(255,143,115,.07); }
        .account-dropdown-logout:disabled { opacity:.55; cursor:default; }
      `}</style>

      <div className="account-menu-wrap" ref={menuRef}>
        <button
          type="button"
          className={`account-menu-trigger ${open ? "open" : ""}`}
          aria-label="Open account menu"
          aria-haspopup="menu"
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
        >
          <span className="avatar">{avatar}</span>
          <span className="account-chevron">⌄</span>
        </button>

        {open && (
          <div className="account-dropdown" role="menu">
            <div className="account-dropdown-profile">
              <div className="account-dropdown-avatar">{avatar}</div>
              <div className="account-dropdown-copy">
                <strong>{name}</strong>
                <span>{email || "Account"}</span>
              </div>
            </div>

            <div className="account-dropdown-divider" />

            <nav className="account-dropdown-nav">
              <Link href="/account" className="account-dropdown-link" onClick={() => setOpen(false)}>
                <span className="account-dropdown-icon">◉</span>
                <span>My Account</span>
              </Link>
              <Link href="/settings" className="account-dropdown-link" onClick={() => setOpen(false)}>
                <span className="account-dropdown-icon">⚙</span>
                <span>Settings</span>
              </Link>
            </nav>

            <div className="account-dropdown-divider" />

            <button
              type="button"
              className="account-dropdown-logout"
              disabled={loggingOut}
              onClick={handleLogout}
            >
              <span className="account-dropdown-icon">↪</span>
              <span>{loggingOut ? "Logging Out..." : "Log Out"}</span>
            </button>
          </div>
        )}
      </div>
    </>
  );
}
