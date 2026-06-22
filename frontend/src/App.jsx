import { Routes, Route, Navigate } from "react-router-dom";

import Navbar from "./components/Navbar.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Pantry from "./pages/Pantry.jsx";
import Profile from "./pages/Profile.jsx";
import PreSurvey from "./pages/PreSurvey.jsx";
import PostSurvey from "./pages/PostSurvey.jsx";
import Recommendations from "./pages/Recommendations.jsx";
import History from "./pages/History.jsx";
import Admin from "./pages/Admin.jsx";

function getUser() {
  return JSON.parse(localStorage.getItem("sp2_user"));
}

function ProtectedRoute({ children }) {
  const user = getUser();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
}

function AdminRoute({ children }) {
  const user = getUser();

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (user.role !== "admin") {
    return <Navigate to="/" replace />;
  }

  return children;
}

function AppLayout({ children }) {
  const user = getUser();

  if (!user) {
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
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />

        <Route
          path="/pantry"
          element={
            <ProtectedRoute>
              <Pantry />
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <Profile />
            </ProtectedRoute>
          }
        />

        <Route
          path="/pre-survey"
          element={
            <ProtectedRoute>
              <PreSurvey />
            </ProtectedRoute>
          }
        />

        <Route
          path="/recommendations"
          element={
            <ProtectedRoute>
              <Recommendations />
            </ProtectedRoute>
          }
        />

        <Route
          path="/history"
          element={
            <ProtectedRoute>
              <History />
            </ProtectedRoute>
          }
        />

        <Route
          path="/post-survey"
          element={
            <ProtectedRoute>
              <PostSurvey />
            </ProtectedRoute>
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
      </Routes>
    </AppLayout>
  );
}
