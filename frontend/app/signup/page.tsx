"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { createClient } from "../../utils/supabase/client";

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [created, setCreated] = useState(false);

  async function handleSignup(event: FormEvent) {
    event.preventDefault();
    setError("");
    setCreated(false);

    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);

    try {
      const supabase = createClient();

      const { data, error: signupError } = await supabase.auth.signUp({
        email: email.trim(),
        password,
        options: {
          data: {
            full_name: name.trim(),
          },
          emailRedirectTo: `${window.location.origin}/auth/confirm`,
        },
      });

      if (signupError) {
        throw signupError;
      }

      if (data.session) {
        window.location.href = "/";
        return;
      }

      setCreated(true);
    } catch (caughtError) {
      setError(
        caughtError instanceof Error
          ? caughtError.message
          : "Could not create your account.",
      );
    } finally {
      setLoading(false);
    }
  }

  if (created) {
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

          .signup-success {
            text-align: center;
            padding: 12px 0 4px;
          }

          .signup-success-icon {
            width: 58px;
            height: 58px;
            margin: 0 auto 14px;
            border-radius: 999px;
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(52, 238, 182, 0.1);
            border: 1px solid rgba(52, 238, 182, 0.18);
            color: var(--mint);
            font-size: 22px;
            font-weight: 900;
          }

          .signup-success h2 {
            margin: 0 0 8px;
          }

          .signup-success p {
            margin: 0 0 18px;
            color: rgba(235, 243, 242, 0.55);
            line-height: 1.6;
            font-size: 13px;
          }

          .signup-success a {
            color: var(--mint);
            font-weight: 800;
            text-decoration: none;
          }
        `}</style>

        <section className="auth-page">
          <section className="glass-card auth-card">
            <div className="signup-success">
              <div className="signup-success-icon">✓</div>
              <h2>Check your email</h2>
              <p>
                We&apos;ve sent a confirmation link to <strong>{email}</strong>.
                Open it to finish creating your Wishlist account.
              </p>
              <Link href="/login">Back to log in</Link>
            </div>
          </section>
        </section>
      </>
    );
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
          width: min(500px, 100%);
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

        .auth-help {
          margin-top: -4px;
          color: rgba(235, 243, 242, 0.38);
          font-size: 10px;
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
          <span className="eyebrow">JOIN WISHLIST</span>
          <h2>Create account</h2>
          <p>Create your account so your tracked products belong only to you.</p>

          <form className="auth-form" onSubmit={handleSignup}>
            <label className="auth-field">
              <span>Name</span>
              <input
                type="text"
                autoComplete="name"
                value={name}
                onChange={(event) => setName(event.target.value)}
                required
              />
            </label>

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
                autoComplete="new-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
                minLength={8}
              />
              <small className="auth-help">Minimum 8 characters.</small>
            </label>

            <label className="auth-field">
              <span>Confirm password</span>
              <input
                type="password"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                required
                minLength={8}
              />
            </label>

            {error && <div className="auth-error">{error}</div>}

            <button className="auth-submit" type="submit" disabled={loading}>
              {loading ? "Creating account..." : "Create account"}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account? <Link href="/login">Log in</Link>
          </div>
        </section>
      </section>
    </>
  );
}
