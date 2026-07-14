import React from "react";

export default function AuthForm({ mode, form, updateField, handleAuth, setMode }) {
  return (
    <div className="auth-card">
      <h2 className="auth-title">
        {mode === "login" ? "Welcome back 👋" : "Create account"}
      </h2>
      <p className="auth-subtitle">
        {mode === "login"
          ? "Sign in to your Exam Prep Studio"
          : "Start your exam preparation journey"}
      </p>

      <form onSubmit={handleAuth}>
        {mode === "register" && (
          <div className="form-group">
            <label htmlFor="auth-name">Full Name</label>
            <input
              id="auth-name"
              type="text"
              className="form-input"
              placeholder="Your name"
              value={form.name}
              onChange={(e) => updateField("name", e.target.value)}
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="auth-email">Email</label>
          <input
            id="auth-email"
            type="email"
            className="form-input"
            placeholder="you@example.com"
            value={form.email}
            onChange={(e) => updateField("email", e.target.value)}
            required
          />
        </div>

        <div className="form-group">
          <label htmlFor="auth-password">Password</label>
          <input
            id="auth-password"
            type="password"
            className="form-input"
            placeholder="••••••••"
            value={form.password}
            onChange={(e) => updateField("password", e.target.value)}
            required
          />
        </div>

        <button type="submit" className="primary-btn">
          {mode === "login" ? "Sign In →" : "Create Account →"}
        </button>
      </form>

      <div className="auth-switch">
        {mode === "login" ? (
          <>Don't have an account?{" "}
            <button onClick={() => setMode("register")}>Register</button>
          </>
        ) : (
          <>Already have an account?{" "}
            <button onClick={() => setMode("login")}>Sign in</button>
          </>
        )}
      </div>
    </div>
  );
}