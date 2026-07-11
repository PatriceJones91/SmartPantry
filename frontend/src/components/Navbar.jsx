import { NavLink, useNavigate } from "react-router-dom";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

export default function Navbar() {
  const navigate = useNavigate();
  const user = getUser();

  function logout() {
    localStorage.removeItem("sp2_user");
    navigate("/login");
  }

  if (!user) {
    return null;
  }

  return (
    <aside className="sidebar">
      <div className="brand navBrandClean">
        <img
          src="/SmartPantry_logo.png"
          alt="Smart Pantry logo"
          className="sidebarLogo"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />
        <div>
          <h2>Smart Pantry</h2>
        </div>
      </div>

      <div className="userBox">
        <strong>{user.username}</strong>
        <span>{user.role}</span>
      </div>

      <nav>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/profile">Profile</NavLink>
        <NavLink to="/pantry">My Pantry</NavLink>
        <NavLink to="/recommendations">Meal Recommendation</NavLink>
        <NavLink to="/history">Recommendation History</NavLink>

        {user.role === "admin" && <NavLink to="/admin">Admin Dashboard</NavLink>}
      </nav>

      <button className="navLogoutButton" onClick={logout}>
        Log Out
      </button>
    </aside>
  );
}
