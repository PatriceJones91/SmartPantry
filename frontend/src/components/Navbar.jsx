import { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const links = [
  { to: "/", label: "Dashboard", icon: "⌂", end: true },
  { to: "/profile", label: "Profile & Preferences", icon: "♙" },
  { to: "/pantry", label: "My Pantry", icon: "🧺" },
  { to: "/recommendations", label: "Meal Recommendations", icon: "🍽" },
  { to: "/history", label: "Recommendation History", icon: "▤" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();
  const [mobileOpen, setMobileOpen] = useState(false);

  function logout() {
    localStorage.removeItem("sp2_user");
    navigate("/login");
  }

  if (!user) return null;

  return (
    <aside className={`sidebar ${mobileOpen ? "mobileNavOpen" : ""}`}>
      <div className="brand navBrandClean">
        <img
          src="/SmartPantry_logo.png"
          alt="Smart Pantry logo"
          className="sidebarLogo"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
        <div><h2>Smart<br />Pantry <small>2.0</small></h2></div>
        <button type="button" className="mobileNavToggle" aria-label={mobileOpen ? "Close navigation menu" : "Open navigation menu"} aria-expanded={mobileOpen} onClick={() => setMobileOpen((open) => !open)}>
          <span aria-hidden="true">{mobileOpen ? "✕" : "☰"}</span>
        </button>
      </div>

      <div className="userBox">
        <strong>{user.username}</strong>
        <span>{user.role}</span>
      </div>

      <nav aria-label="Main navigation">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end} onClick={() => setMobileOpen(false)}>
            <span className="navIcon" aria-hidden="true">{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
        {user.role === "admin" && (
          <NavLink to="/admin" onClick={() => setMobileOpen(false)}>
            <span className="navIcon" aria-hidden="true">◆</span>
            <span>Admin Dashboard</span>
          </NavLink>
        )}

        <button type="button" className="navLogoutButton navLogoutInline" onClick={logout}>
          <span className="navIcon" aria-hidden="true">↪</span>
          <span>Log Out</span>
        </button>
      </nav>
    </aside>
  );
}
