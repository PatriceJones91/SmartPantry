import { Routes, Route, Navigate, useLocation } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Pantry from "./pages/Pantry.jsx";
import Profile from "./pages/Profile.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import History from "./pages/History.jsx";
import Admin from "./pages/Admin.jsx";
import Committee from "./pages/Committee.jsx";

function getUser() {
  try {
    return JSON.parse(localStorage.getItem("sp2_user"));
  } catch {
    return null;
  }
}

function roleHome(user) {
  if (!user) return "/login";
  if (user.role === "admin") return "/admin";
  if (user.role === "committee") return "/committee";
  return "/";
}

function ParticipantRoute({ children }) {
  const user = getUser();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "participant") {
    return <Navigate to={roleHome(user)} replace />;
  }

  return children;
}

function AdminRoute({ children }) {
  const user = getUser();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "admin") {
    return <Navigate to={roleHome(user)} replace />;
  }

  return children;
}

function CommitteeRoute({ children }) {
  const user = getUser();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (!['admin', 'committee'].includes(user.role)) {
    return <Navigate to={roleHome(user)} replace />;
  }

  return children;
}

function RoleHomeRedirect() {
  return <Navigate to={roleHome(getUser())} replace />;
}

function AppLayout({ children }) {
  const location = useLocation();
  const user = getUser();
  const isLoginPage = location.pathname === "/login";

  if (isLoginPage || !user) {
    return children;
  }

  return (
    <div className="appShell">
      <Navbar />
      <main className="mainContent">{children}</main>
    </div>
  );
}

export default function App() {
  return (
    <AppLayout>
      <Routes>
        <Route path="/login" element={<Login />} />

        <Route
          path="/"
          element={
            <ParticipantRoute>
              <Dashboard />
            </ParticipantRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ParticipantRoute>
              <Profile />
            </ParticipantRoute>
          }
        />

        <Route
          path="/pantry"
          element={
            <ParticipantRoute>
              <Pantry />
            </ParticipantRoute>
          }
        />

        <Route
          path="/recommendations"
          element={
            <ParticipantRoute>
              <Recommendations />
            </ParticipantRoute>
          }
        />

        <Route
          path="/history"
          element={
            <ParticipantRoute>
              <History />
            </ParticipantRoute>
          }
        />

        <Route
          path="/admin"
          element={
            <AdminRoute>
              <Admin />
            </AdminRoute>
          }
        />

        <Route
          path="/committee"
          element={
            <CommitteeRoute>
              <Committee />
            </CommitteeRoute>
          }
        />

        <Route path="/pre-survey" element={<RoleHomeRedirect />} />
        <Route path="/post-survey" element={<RoleHomeRedirect />} />
        <Route path="/feedback" element={<RoleHomeRedirect />} />
        <Route path="*" element={<RoleHomeRedirect />} />
      </Routes>
    </AppLayout>
  );
}
