"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { createClient } from "../../utils/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleLogin(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");

    try {
      const supabase = createClient();

      const { error: loginError } = await supabase.auth.signInWithPassword({
        email: email.trim(),
        password,
      });

      if (loginError) {
        throw loginError;
      }

      router.push("/");
      router.refresh();
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not log in.",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <style jsx global>{`
        .auth-page {
          min-height: calc(100vh - 150px);
          display: flex;
          align-items: center;
          justify-content: center;
          padding: 24px 0 48px;
        }

        .auth-card {
          width: min(460px, 100%);
          padding: 28px;
        }

        .auth-card h2 {
          margin: 5px 0 7px;
          font-size: 32px;
        }

        .auth-card > p {
          margin: 0 0 24px;
          color: rgba(235, 243, 242, 0.55);
          line-height: 1.55;
          font-size: 13px;
        }

        .auth-form {
          display: grid;
          gap: 15px;
        }

        .auth-field {
          display: grid;
          gap: 7px;
        }

        .auth-field span {
          color: rgba(235, 243, 242, 0.55);
          font-size: 10px;
          font-weight: 800;
          letter-spacing: 0.07em;
          text-transform: uppercase;
        }

        .auth-field input {
          width: 100%;
          height: 48px;
          padding: 0 14px;
          box-sizing: border-box;
          border-radius: 11px;
          border: 1px solid rgba(255, 255, 255, 0.09);
          background: rgba(4, 14, 16, 0.72);
          color: rgba(248, 251, 250, 0.96);
          outline: none;
          font: inherit;
        }

        .auth-field input:focus {
          border-color: rgba(52, 238, 182, 0.35);
          box-shadow: 0 0 0 3px rgba(52, 238, 182, 0.07);
        }

        .auth-submit {
          min-height: 48px;
          border: 0;
          border-radius: 11px;
          background: var(--mint);
          color: #07110f;
          font: inherit;
          font-size: 13px;
          font-weight: 900;
          cursor: pointer;
        }

        .auth-submit:disabled {
          opacity: 0.55;
          cursor: wait;
        }

        .auth-error {
          padding: 12px 13px;
          border-radius: 10px;
          border: 1px solid rgba(255, 143, 115, 0.18);
          background: rgba(255, 143, 115, 0.07);
          color: #ffab97;
          font-size: 12px;
          line-height: 1.45;
        }

        .auth-footer {
          margin-top: 20px;
          padding-top: 18px;
          border-top: 1px solid rgba(255, 255, 255, 0.06);
          color: rgba(235, 243, 242, 0.52);
          font-size: 12px;
          text-align: center;
        }

        .auth-footer a {
          color: var(--mint);
          font-weight: 800;
          text-decoration: none;
        }
      `}</style>

      <section className="auth-page">
        <section className="glass-card auth-card">
          <span className="eyebrow">WELCOME BACK</span>
          <h2>Log in</h2>
          <p>Sign in to access your Wishlist products, history and alerts.</p>

          <form className="auth-form" onSubmit={handleLogin}>
            <label className="auth-field">
              <span>Email</span>
              <input
                type="email"
                autoComplete="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>

            <label className="auth-field">
              <span>Password</span>
              <input
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? "Logging in..." : "Log in"}
            </button>
          </form>

          <div className="auth-footer">
            New to Wishlist? <Link href="/signup">Create an account</Link>
          </div>
        </section>
      </section>
    </>
  );
}
