import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

function UserIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 21a8 8 0 0 0-16 0" />
      <circle cx="12" cy="7" r="4" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="5" y="10" width="14" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3" />
    </svg>
  );
}

function EyeIcon({ open }) {
  return open ? (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="m3 3 18 18" />
      <path d="M10.6 6.2A10.8 10.8 0 0 1 12 6c6.5 0 10 6 10 6a17 17 0 0 1-3 3.8" />
      <path d="M6.6 6.6C3.7 8.4 2 12 2 12s3.5 6 10 6c1.7 0 3.2-.4 4.5-1" />
    </svg>
  );
}

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const isRegister = mode === "register";

  function switchMode(nextMode) {
    setMode(nextMode);
    setError("");
    setPassword("");
    setConfirmPassword("");
    setShowPassword(false);
    setShowConfirmPassword(false);
  }

  async function submit(e) {
    e.preventDefault();
    setError("");

    const cleanUsername = username.trim();

    if (!cleanUsername || !password) {
      setError("Please enter your username and password.");
      return;
    }

    if (isRegister && password.length < 6) {
      setError("Your password must be at least 6 characters.");
      return;
    }

    if (isRegister && password !== confirmPassword) {
      setError("The passwords do not match. Please try again.");
      return;
    }

    setLoading(true);

    try {
      if (isRegister) {
        await api.register({
          username: cleanUsername,
          password,
          role: "participant",
        });
      }

      const user = await api.login({ username: cleanUsername, password });
      localStorage.setItem("sp2_user", JSON.stringify(user));
      navigate("/");
    } catch (err) {
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="authPage">
      <span className="authDecoration authLeafOne" aria-hidden="true">⌁</span>
      <span className="authDecoration authLeafTwo" aria-hidden="true">⌁</span>
      <span className="authDecoration authApple" aria-hidden="true">○</span>

      <section className="authCard" aria-labelledby="auth-title">
        <img
          src="/SmartPantry_logo.png"
          alt="Smart Pantry"
          className="authLogo"
          onError={(e) => {
            e.currentTarget.style.display = "none";
          }}
        />

        <header className="authHeader">
          <h1 id="auth-title">
            {isRegister ? "Create Your Smart Pantry Account" : "Welcome to Smart Pantry!!!"}
          </h1>
          <p>
            {isRegister
              ? "Create your participant account to track pantry items, complete study activities, and receive personalized meal recommendations."
              : "Log in to track your pantry items, complete study activities, and receive meal recommendations."}
          </p>
        </header>

        <form onSubmit={submit} className="authForm">
          <div className="authField">
            <label htmlFor="username">Username</label>
            <div className="authInputWrap">
              <span className="authInputIcon"><UserIcon /></span>
              <input
                id="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter a username"
                autoComplete="username"
                minLength={3}
                maxLength={32}
                required
              />
            </div>
          </div>

          <div className="authField">
            <label htmlFor="password">Password</label>
            <div className="authInputWrap">
              <span className="authInputIcon"><LockIcon /></span>
              <input
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter a password"
                type={showPassword ? "text" : "password"}
                autoComplete={isRegister ? "new-password" : "current-password"}
                minLength={6}
                maxLength={64}
                required
              />
              <button
                type="button"
                className="passwordToggle"
                onClick={() => setShowPassword((current) => !current)}
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
            {isRegister && <small>Use at least 6 characters.</small>}
          </div>

          {isRegister && (
            <div className="authField">
              <label htmlFor="confirmPassword">Confirm Password</label>
              <div className="authInputWrap">
                <span className="authInputIcon"><LockIcon /></span>
                <input
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter your password"
                  type={showConfirmPassword ? "text" : "password"}
                  autoComplete="new-password"
                  minLength={6}
                  maxLength={64}
                  required
                />
                <button
                  type="button"
                  className="passwordToggle"
                  onClick={() => setShowConfirmPassword((current) => !current)}
                  aria-label={showConfirmPassword ? "Hide confirmed password" : "Show confirmed password"}
                >
                  <EyeIcon open={showConfirmPassword} />
                </button>
              </div>
            </div>
          )}

          {error && <p className="authError" role="alert">{error}</p>}

          <button type="submit" className="authPrimaryButton" disabled={loading}>
            {loading ? "Please wait..." : isRegister ? "Create Account" : "Log In"}
          </button>
        </form>

        <aside className="authHelpBox">
          <span className="authHelpIcon" aria-hidden="true">?</span>
          <div>
            <strong>{isRegister ? "Need help creating your account?" : "Need help logging in?"}</strong>
            <p>
              {isRegister
                ? "Contact the study administrator if you receive an error or cannot complete registration."
                : "Contact the study administrator if you forgot your password or cannot access your account."}
            </p>
          </div>
        </aside>

        <div className="authSwitchArea">
          <span className="authDivider"><span>or</span></span>
          <p>
            {isRegister ? "Already have an account?" : "New participant?"}{" "}
            <button
              type="button"
              className="authTextButton"
              onClick={() => switchMode(isRegister ? "login" : "register")}
            >
              {isRegister ? "Log in" : "Create an account"}
            </button>
          </p>
        </div>
      </section>
    </div>
  );
}
