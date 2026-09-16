import { NavLink, Link } from "react-router-dom";
import { useState } from "react";

const THEMES = [
  { name: "cursor", bg: "#f2f1ed", border: "#cf2d56" },
  { name: "nord", bg: "#eceff4", border: "#81a1c1" },
  { name: "sepia", bg: "#faf0e6", border: "#d4c4a8" },
  { name: "ocean", bg: "#f0f6fc", border: "#93b4d3" },
  { name: "forest", bg: "#f4f7f2", border: "#95b889" },
];

export default function Sidebar() {
  const [collapsed, setCollapsed] = useState(false);

  const setTheme = (theme) => {
    document.body.setAttribute("data-theme", theme);
  };

  return (
    <aside className={`sidebar${collapsed ? " collapsed" : ""}`}>
      {/* Brand */}
      <div className="brand">
        <Link to="/" className="brand-text-wrapper" style={{ textDecoration: "none" }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}>
            <defs>
              <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f54e00" />
                <stop offset="100%" stopColor="#cf2d56" />
              </linearGradient>
            </defs>
            {/* Eggs */}
            <circle cx="9" cy="11" r="2.5" stroke="url(#logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
            <circle cx="15" cy="11" r="2.5" stroke="url(#logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
            <circle cx="12" cy="13" r="2.5" stroke="url(#logo-grad)" fill="rgba(245, 78, 0, 0.08)" />
            {/* Woven Twigs base */}
            <path d="M3 13c1 5 17 5 18 0" stroke="url(#logo-grad)" />
            <path d="M5 15c2 4 12 4 14 0" stroke="url(#logo-grad)" />
            <path d="M7 17c1.5 3 8.5 3 10 0" stroke="url(#logo-grad)" />
          </svg>
          <span
            className="brand-text"
            style={{
              background: "linear-gradient(135deg, #f54e00 0%, #cf2d56 100%)",
              WebkitBackgroundClip: "text",
              WebkitTextFillColor: "transparent",
              fontWeight: 800,
            }}
          >
            EchoTrack
          </span>
        </Link>
        <button
          className="icon-btn sidebar-toggle"
          onClick={() => setCollapsed((c) => !c)}
          style={{ width: 32, height: 32, transition: "transform 0.3s" }}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M15 18l-6-6 6-6" />
          </svg>
        </button>
      </div>

      {/* Mission Control */}
      <div className="nav-section">
        <div className="text-xs text-muted nav-text" style={{ padding: "0 12px", marginBottom: 8 }}>Mission Control</div>
        {[
          { to: "/", label: "Dashboard", icon: "📅" },
          { to: "/commitments", label: "Pursuits", icon: "🎯" },
          { to: "/knowledge", label: "Knowledge", icon: "🧠" },
        ].map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            style={{ textDecoration: "none" }}
          >
            <span style={{ fontSize: 16, width: 24, textAlign: "center" }}>{icon}</span>
            <span className="nav-text">{label}</span>
          </NavLink>
        ))}
      </div>

      {/* Media */}
      <div className="nav-section">
        <div className="text-xs text-muted nav-text" style={{ padding: "0 12px", marginBottom: 8 }}>Media</div>
        {[
          { to: "/photos", label: "Photos", icon: "📷" },
          { to: "/videos", label: "Videos", icon: "🎬" },
          { to: "/books", label: "Books", icon: "📚" },
        ].map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) => `nav-item${isActive ? " active" : ""}`}
            style={{ textDecoration: "none" }}
          >
            <span style={{ fontSize: 16, width: 24, textAlign: "center" }}>{icon}</span>
            <span className="nav-text">{label}</span>
          </NavLink>
        ))}
      </div>

      {/* Theme switcher */}
      <div className="nav-section" style={{ marginTop: "auto" }}>
        <div className="text-xs text-muted nav-text" style={{ padding: "0 12px", marginBottom: 8 }}>Theme</div>
        <div className="theme-dots nav-text" style={{ display: "flex", gap: 8, padding: "0 12px", flexWrap: "wrap" }}>
          {THEMES.map((t) => (
            <div
              key={t.name}
              className="theme-dot"
              style={{ background: t.bg, border: `2px solid ${t.border}` }}
              onClick={() => setTheme(t.name)}
              title={t.name.charAt(0).toUpperCase() + t.name.slice(1)}
            />
          ))}
        </div>
      </div>
    </aside>
  );
}
