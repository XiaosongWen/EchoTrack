import Sidebar from "./Sidebar";
import { useAuthStore } from "../stores/authStore";

export default function Layout({ children }) {
  const { user, signOut } = useAuthStore();

  return (
    <>
      <Sidebar />
      <main className="main-container">
        <header className="app-header">
          <div className="search-bar">
            <span style={{ fontSize: "16px" }}>🔍</span>
            <input type="text" placeholder="Search commitments, logs, or type a command... (Cmd+K)" />
          </div>
          <div className="header-actions" style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            {user?.email && (
              <span style={{ fontSize: "12px", color: "var(--text-muted, #94a3b8)" }}>
                {user.email}
              </span>
            )}
            <button className="icon-btn" style={{ fontSize: "18px" }}>🔔</button>
            <div className="user-profile" title={user?.email || "User"}>
              <img src="https://avatars.githubusercontent.com/u/6759395?v=4" alt="User" />
            </div>
            <button
              onClick={signOut}
              title="Sign Out"
              style={{
                background: "transparent",
                border: "1px solid var(--border-color, #334155)",
                color: "var(--text-muted, #94a3b8)",
                borderRadius: "6px",
                padding: "4px 10px",
                fontSize: "12px",
                cursor: "pointer",
              }}
            >
              Sign out
            </button>
          </div>
        </header>
        {children}
      </main>
    </>
  );
}
