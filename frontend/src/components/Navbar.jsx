import { NavLink, useNavigate } from "react-router-dom";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

const links = [
  { to: "/", label: "Dashboard", icon: "⌂", end: true },
  { to: "/pantry", label: "My Pantry", icon: "🧺" },
  { to: "/recommendations", label: "Meal Recommendations", icon: "🍽" },
  { to: "/history", label: "Recommendation History", icon: "▤" },
  { to: "/profile", label: "Profile & Preferences", icon: "♙" },
];

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();

  function logout() {
    localStorage.removeItem("sp2_user");
    navigate("/login");
  }

  if (!user) return null;

  return (
    <aside className="sidebar">
      <div className="brand navBrandClean">
        <img
          src="/SmartPantry_logo.png"
          alt="Smart Pantry logo"
          className="sidebarLogo"
          onError={(e) => { e.currentTarget.style.display = "none"; }}
        />
        <div><h2>Smart<br />Pantry <small>2.0</small></h2></div>
      </div>

      <div className="userBox">
        <strong>{user.username}</strong>
        <span>{user.role}</span>
      </div>

      <nav aria-label="Main navigation">
        {links.map((link) => (
          <NavLink key={link.to} to={link.to} end={link.end}>
            <span className="navIcon" aria-hidden="true">{link.icon}</span>
            <span>{link.label}</span>
          </NavLink>
        ))}
        {user.role === "admin" && (
          <NavLink to="/admin">
            <span className="navIcon" aria-hidden="true">◆</span>
            <span>Admin Dashboard</span>
          </NavLink>
        )}
      </nav>

      <button className="navLogoutButton" onClick={logout}>
        <span aria-hidden="true">↪</span> Log Out
      </button>
    </aside>
  );
}
