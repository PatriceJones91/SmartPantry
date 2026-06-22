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
      <div className="brand">
        <div className="logo">🥤</div>
        <div>
          <h2>Smart Pantry</h2>
          <p>2.0 React + API</p>
        </div>
      </div>

      <div className="userBox">
        <strong>{user.username}</strong>
        <span>{user.role}</span>
      </div>

      <nav>
        <NavLink to="/">Dashboard</NavLink>
        <NavLink to="/pantry">My Pantry</NavLink>
        <NavLink to="/profile">Profile</NavLink>
        <NavLink to="/pre-survey">Pre-Study Survey</NavLink>
        <NavLink to="/recommendations">Recommendations</NavLink>
        <NavLink to="/history">History</NavLink>
        <NavLink to="/post-survey">Post-Study Survey</NavLink>

        {user.role === "admin" && (
          <NavLink to="/admin">Admin Dashboard</NavLink>
        )}
      </nav>

      <button className="ghostButton" onClick={logout}>
        Logout
      </button>
    </aside>
  );
}
