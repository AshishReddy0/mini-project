// Minimal connectivity UI for Phase 2 — proves frontend, backend, and DB work together.
// Full screens (revision, exam, quiz, chat) will be built in Phase 4.

import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api.js";

const defaultForm = {
  name: "",
  email: "",
  password: "",
  workspaceName: "",
};

export default function App() {
  const [form, setForm] = useState(defaultForm);
  const [apiStatus, setApiStatus] = useState("checking...");
  const [dbStatus, setDbStatus] = useState("checking...");
  const [user, setUser] = useState(null);
  const [workspaces, setWorkspaces] = useState([]);
  const [message, setMessage] = useState("");
  const [mode, setMode] = useState("login"); // login | register

  // Check API and database health on page load
  useEffect(() => {
    async function checkHealth() {
      try {
        const health = await api.health();
        setApiStatus(health.status);
      } catch {
        setApiStatus("unreachable");
      }

      try {
        const dbHealth = await api.healthDb();
        setDbStatus(dbHealth.database);
      } catch {
        setDbStatus("unreachable");
      }
    }

    checkHealth();

    // Restore session if a token was saved earlier
    if (getToken()) {
      api
        .me()
        .then(setUser)
        .catch(() => setToken(null));
    }
  }, []);

  function updateField(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleAuth(event) {
    event.preventDefault();
    setMessage("");

    try {
      if (mode === "register") {
        await api.register({
          name: form.name,
          email: form.email,
          password: form.password,
        });
        setMessage("Account created. You can log in now.");
        setMode("login");
        return;
      }

      const result = await api.login({
        email: form.email,
        password: form.password,
      });
      setToken(result.access_token);
      const profile = await api.me();
      setUser(profile);
      setMessage("Logged in successfully.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function handleCreateWorkspace(event) {
    event.preventDefault();
    setMessage("");

    try {
      await api.createWorkspace({ name: form.workspaceName });
      updateField("workspaceName", "");
      await loadWorkspaces();
      setMessage("Workspace created.");
    } catch (error) {
      setMessage(error.message);
    }
  }

  async function loadWorkspaces() {
    const data = await api.listWorkspaces();
    setWorkspaces(data);
  }

  function handleLogout() {
    setToken(null);
    setUser(null);
    setWorkspaces([]);
    setMessage("Logged out.");
  }

  return (
    <div className="app">
      <header>
        <h1>Study Companion</h1>
        <p>Phase 2 connectivity test — frontend, backend, and database</p>
      </header>

      <section className="card">
        <h2>System Status</h2>
        <p>
          API: <span className={apiStatus === "ok" ? "ok" : "error"}>{apiStatus}</span>
        </p>
        <p>
          Database:{" "}
          <span className={dbStatus === "connected" ? "ok" : "error"}>{dbStatus}</span>
        </p>
      </section>

      {!user ? (
        <section className="card">
          <h2>{mode === "login" ? "Login" : "Register"}</h2>
          <form onSubmit={handleAuth}>
            {mode === "register" && (
              <input
                type="text"
                placeholder="Name"
                value={form.name}
                onChange={(e) => updateField("name", e.target.value)}
                required
              />
            )}
            <input
              type="email"
              placeholder="Email"
              value={form.email}
              onChange={(e) => updateField("email", e.target.value)}
              required
            />
            <input
              type="password"
              placeholder="Password"
              value={form.password}
              onChange={(e) => updateField("password", e.target.value)}
              required
            />
            <button type="submit">{mode === "login" ? "Login" : "Register"}</button>
          </form>
          <button
            type="button"
            className="link-btn"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "Need an account? Register" : "Have an account? Login"}
          </button>
        </section>
      ) : (
        <>
          <section className="card">
            <h2>Welcome, {user.name}</h2>
            <p>{user.email}</p>
            <button type="button" onClick={handleLogout}>
              Logout
            </button>
          </section>

          <section className="card">
            <h2>Create Workspace</h2>
            <form onSubmit={handleCreateWorkspace}>
              <input
                type="text"
                placeholder="Workspace name (e.g. Operating Systems)"
                value={form.workspaceName}
                onChange={(e) => updateField("workspaceName", e.target.value)}
                required
              />
              <button type="submit">Create Workspace</button>
            </form>
            <button type="button" onClick={loadWorkspaces}>
              Refresh Workspaces
            </button>
            <ul>
              {workspaces.map((ws) => (
                <li key={ws.id}>
                  <strong>{ws.name}</strong>
                  {ws.description ? ` — ${ws.description}` : ""}
                </li>
              ))}
            </ul>
          </section>
        </>
      )}

      {message && <p className="message">{message}</p>}
    </div>
  );
}
