export default function WorkspacePanel({
  form,
  updateField,
  handleCreateWorkspace,
  loadWorkspaces,
  workspaces,
  handleSelectWorkspace,
}) {
  return (
    <section className="card">
      <h2>Create Workspace</h2>

      <form onSubmit={handleCreateWorkspace}>
        <input
          type="text"
          placeholder="Workspace name (e.g. Operating Systems)"
          value={form.workspaceName}
          onChange={(e) =>
            updateField("workspaceName", e.target.value)
          }
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
            <button
              type="button"
              onClick={() => handleSelectWorkspace(ws)}
            >
              {ws.name}
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}