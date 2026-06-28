export default function AuthForm({
  mode,
  form,
  updateField,
  handleAuth,
  setMode,
}) {
  return (
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

        <button type="submit">
          {mode === "login" ? "Login" : "Register"}
        </button>
      </form>

      <button
        type="button"
        className="link-btn"
        onClick={() =>
          setMode(mode === "login" ? "register" : "login")
        }
      >
        {mode === "login"
          ? "Need an account? Register"
          : "Have an account? Login"}
      </button>
    </section>
  );
}