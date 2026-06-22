import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client.js";

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("participant");
  const [error, setError] = useState("");
  async function submit(e) { e.preventDefault(); setError(""); try { const user = mode === "login" ? await api.login({ username, password }) : await api.register({ username, password, role }); localStorage.setItem("sp2_user", JSON.stringify(user)); navigate("/"); } catch (err) { setError(err.message); } }
  return <div className="loginPage"><div className="loginCard"><h1>Welcome to Smart Pantry</h1><p>Track pantry items, view alerts, and get meal ideas.</p><form onSubmit={submit}><label>Username</label><input value={username} onChange={(e) => setUsername(e.target.value)} /><label>Password</label><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />{mode === "register" && <><label>Role</label><select value={role} onChange={(e) => setRole(e.target.value)}><option value="participant">participant</option><option value="admin">admin</option></select></>}{error && <div className="error">{error}</div>}<button type="submit">{mode === "login" ? "Login" : "Create Account"}</button></form><button className="linkButton" onClick={() => setMode(mode === "login" ? "register" : "login")}>{mode === "login" ? "Create a participant account" : "Back to login"}</button><p className="hint">Demo admin: admin / Admin123!</p></div></div>;
}
