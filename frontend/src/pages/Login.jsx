import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  async function submit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      if (isRegister) {
        await api.register({
          username,
          password,
          role: "participant",
        });
      }

      const user = await api.login({ username, password });
      localStorage.setItem("sp2_user", JSON.stringify(user));
      navigate("/");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="brightLoginPage">
      <section className="brightLoginCard">
        <img
          src="/SmartPantry_logo.png"
          alt="Smart Pantry logo"
          className="brightLoginLogo"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />

        <form onSubmit={submit} className="brightLoginForm">
          <div className="loginField">
            <label>Username</label>
            <input
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="Enter username"
              autoComplete="username"
            />
          </div>

          <div className="loginField">
            <label>Password</label>
            <input
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter password"
              type="password"
              autoComplete={isRegister ? "new-password" : "current-password"}
            />
          </div>

          {error && <p className="error">{error}</p>}

          <button type="submit" disabled={loading}>
            {loading ? "Please wait..." : isRegister ? "Create Account" : "Login"}
          </button>
        </form>

        <div className="loginCreateArea">
          {isRegister ? (
            <>
              <span>Already have an account?</span>
              <button type="button" onClick={() => setMode("login")}>
                Back to Login
              </button>
            </>
          ) : (
            <>
              <span>New participant?</span>
              <button type="button" onClick={() => setMode("register")}>
                Create Account
              </button>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
