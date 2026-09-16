import React, { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";

const THEMES = [
  { name: "cursor", bg: "#f2f1ed", border: "#cf2d56", title: "Cursor" },
  { name: "nord", bg: "#eceff4", border: "#81a1c1", title: "Nord" },
  { name: "sepia", bg: "#faf0e6", border: "#d4c4a8", title: "Sepia" },
  { name: "ocean", bg: "#f0f6fc", border: "#93b4d3", title: "Ocean" },
  { name: "forest", bg: "#f4f7f2", border: "#95b889", title: "Forest" },
];

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const signIn = useAuthStore((state) => state.signIn);
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/";

  const setTheme = (theme) => {
    document.body.setAttribute("data-theme", theme);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage("");
    setLoading(true);

    try {
      const res = await signIn(email, password);
      if (!res.success) {
        setErrorMessage(res.error || "Invalid login credentials. Please try again.");
      } else {
        navigate(from, { replace: true });
      }
    } catch (err) {
      setErrorMessage(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.page}>
      {/* Background Decorative Ambient Blobs */}
      <div style={styles.ambientBlob1} />
      <div style={styles.ambientBlob2} />

      {/* Top Bar with Theme Switcher */}
      <div style={styles.topBar}>
        <div style={styles.themeSelector}>
          {THEMES.map((t) => (
            <button
              key={t.name}
              onClick={() => setTheme(t.name)}
              title={`Switch to ${t.title} theme`}
              style={{
                ...styles.themeDot,
                backgroundColor: t.bg,
                borderColor: t.border,
              }}
            />
          ))}
        </div>
      </div>

      <div style={styles.cardContainer}>
        <div style={styles.card}>
          {/* Logo & Header */}
          <div style={styles.header}>
            <div style={styles.logoWrapper}>
              <svg
                width="36"
                height="36"
                viewBox="0 0 24 24"
                fill="none"
                strokeWidth="2.2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <defs>
                  <linearGradient id="login-logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stopColor="#f54e00" />
                    <stop offset="100%" stopColor="#cf2d56" />
                  </linearGradient>
                </defs>
                <circle cx="9" cy="11" r="2.5" stroke="url(#login-logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
                <circle cx="15" cy="11" r="2.5" stroke="url(#login-logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
                <circle cx="12" cy="13" r="2.5" stroke="url(#login-logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
                <path d="M3 13c1 5 17 5 18 0" stroke="url(#login-logo-grad)" />
                <path d="M5 15c2 4 12 4 14 0" stroke="url(#login-logo-grad)" />
                <path d="M7 17c1.5 3 8.5 3 10 0" stroke="url(#login-logo-grad)" />
              </svg>
            </div>
            <h1 style={styles.brandTitle}>Nest</h1>
            <p style={styles.brandSubtitle}>Welcome back. Sign in to your workspace.</p>
          </div>

          {/* Error Alert */}
          {errorMessage && (
            <div style={styles.errorAlert}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} style={styles.form}>
            <div style={styles.fieldGroup}>
              <label style={styles.label}>Email Address</label>
              <div style={styles.inputWrapper}>
                <span style={styles.inputIcon}>✉️</span>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  autoComplete="email"
                  required
                  style={styles.input}
                />
              </div>
            </div>

            <div style={styles.fieldGroup}>
              <div style={styles.labelRow}>
                <label style={styles.label}>Password</label>
              </div>
              <div style={styles.inputWrapper}>
                <span style={styles.inputIcon}>🔒</span>
                <input
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete="current-password"
                  required
                  style={{ ...styles.input, paddingRight: "40px" }}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  style={styles.togglePasswordBtn}
                  title={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "🙈" : "👁️"}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              style={{
                ...styles.submitBtn,
                opacity: loading ? 0.75 : 1,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              {loading ? (
                <span style={styles.loadingContainer}>
                  <span style={styles.spinner} />
                  Signing in...
                </span>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          {/* Footer Info */}
          <div style={styles.footer}>
            <span style={styles.footerText}>
              Powered by <strong style={{ color: "var(--fg, #26251e)" }}>Supabase Auth</strong>
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
    minHeight: "100vh",
    width: "100vw",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "var(--bg, #f2f1ed)",
    color: "var(--fg, #26251e)",
    fontFamily: "var(--font-main, 'Instrument Sans', -apple-system, sans-serif)",
    position: "relative",
    overflow: "hidden",
    padding: "24px",
    boxSizing: "border-box",
  },
  ambientBlob1: {
    position: "absolute",
    top: "-15%",
    left: "-10%",
    width: "50vw",
    height: "50vw",
    maxWidth: "500px",
    maxHeight: "500px",
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(245, 78, 0, 0.12) 0%, rgba(245, 78, 0, 0) 70%)",
    filter: "blur(40px)",
    pointerEvents: "none",
    zIndex: 0,
  },
  ambientBlob2: {
    position: "absolute",
    bottom: "-15%",
    right: "-10%",
    width: "50vw",
    height: "50vw",
    maxWidth: "550px",
    maxHeight: "550px",
    borderRadius: "50%",
    background: "radial-gradient(circle, rgba(207, 45, 86, 0.10) 0%, rgba(207, 45, 86, 0) 70%)",
    filter: "blur(50px)",
    pointerEvents: "none",
    zIndex: 0,
  },
  topBar: {
    position: "absolute",
    top: "24px",
    right: "24px",
    zIndex: 10,
  },
  themeSelector: {
    display: "flex",
    alignItems: "center",
    gap: "8px",
    padding: "6px 10px",
    backgroundColor: "var(--surface, #e6e5e0)",
    borderRadius: "20px",
    border: "1px solid var(--border-light, #e6e5e0)",
    boxShadow: "0 2px 8px rgba(0, 0, 0, 0.04)",
  },
  themeDot: {
    width: "16px",
    height: "16px",
    borderRadius: "50%",
    borderWidth: "2px",
    borderStyle: "solid",
    padding: 0,
    cursor: "pointer",
    transition: "transform 0.15s ease",
  },
  cardContainer: {
    width: "100%",
    maxWidth: "420px",
    zIndex: 1,
    margin: "auto",
  },
  card: {
    backgroundColor: "var(--surface-raised, #ffffff)",
    borderRadius: "24px",
    padding: "40px 36px",
    boxShadow: "0 20px 40px -15px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04)",
    border: "1px solid var(--border-light, #e6e5e0)",
    display: "flex",
    flexDirection: "column",
    gap: "24px",
    backdropFilter: "blur(12px)",
  },
  header: {
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
  },
  logoWrapper: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    width: "56px",
    height: "56px",
    borderRadius: "16px",
    backgroundColor: "var(--surface, #f2f1ed)",
    marginBottom: "14px",
    boxShadow: "inset 0 1px 2px rgba(0,0,0,0.05)",
  },
  brandTitle: {
    fontSize: "26px",
    fontWeight: "800",
    letterSpacing: "-0.6px",
    margin: 0,
    background: "linear-gradient(135deg, #f54e00 0%, #cf2d56 100%)",
    WebkitBackgroundClip: "text",
    WebkitTextFillColor: "transparent",
  },
  brandSubtitle: {
    fontSize: "14px",
    color: "var(--fg-muted, #6b6b6b)",
    marginTop: "6px",
    marginBotton: 0,
    lineHeight: "1.4",
  },
  errorAlert: {
    display: "flex",
    alignItems: "center",
    gap: "10px",
    padding: "12px 14px",
    backgroundColor: "rgba(207, 45, 86, 0.08)",
    border: "1px solid rgba(207, 45, 86, 0.25)",
    borderRadius: "12px",
    color: "var(--danger, #cf2d56)",
    fontSize: "13px",
    lineHeight: "1.4",
  },
  form: {
    display: "flex",
    flexDirection: "column",
    gap: "18px",
  },
  fieldGroup: {
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  labelRow: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  label: {
    fontSize: "13px",
    fontWeight: "600",
    color: "var(--fg, #26251e)",
    letterSpacing: "-0.2px",
  },
  inputWrapper: {
    position: "relative",
    display: "flex",
    alignItems: "center",
  },
  inputIcon: {
    position: "absolute",
    left: "12px",
    fontSize: "14px",
    pointerEvents: "none",
    opacity: 0.6,
  },
  input: {
    width: "100%",
    padding: "12px 14px 12px 38px",
    fontSize: "14px",
    fontFamily: "inherit",
    borderRadius: "12px",
    border: "1px solid var(--border-light, #e6e5e0)",
    backgroundColor: "var(--surface, #f2f1ed)",
    color: "var(--fg, #26251e)",
    outline: "none",
    transition: "border-color 0.15s ease, box-shadow 0.15s ease",
    boxSizing: "border-box",
  },
  togglePasswordBtn: {
    position: "absolute",
    right: "12px",
    background: "none",
    border: "none",
    cursor: "pointer",
    fontSize: "14px",
    padding: "4px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    opacity: 0.7,
  },
  submitBtn: {
    marginTop: "6px",
    width: "100%",
    padding: "13px",
    fontSize: "15px",
    fontWeight: "600",
    fontFamily: "inherit",
    borderRadius: "12px",
    border: "none",
    background: "linear-gradient(135deg, #f54e00 0%, #cf2d56 100%)",
    color: "#ffffff",
    boxShadow: "0 6px 16px rgba(245, 78, 0, 0.25)",
    transition: "transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease",
  },
  loadingContainer: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "8px",
  },
  spinner: {
    width: "14px",
    height: "14px",
    border: "2px solid rgba(255, 255, 255, 0.35)",
    borderTopColor: "#ffffff",
    borderRadius: "50%",
    display: "inline-block",
    animation: "spin 0.7s linear infinite",
  },
  footer: {
    textAlign: "center",
    paddingTop: "6px",
    borderTop: "1px solid var(--border-light, #e6e5e0)",
  },
  footerText: {
    fontSize: "12px",
    color: "var(--fg-muted, #6b6b6b)",
  },
};
