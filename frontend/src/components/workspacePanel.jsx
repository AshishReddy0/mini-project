export default function WorkspacePanel({
  form,
  updateField,
  handleCreateWorkspace,
  loadWorkspaces,
  workspaces,
  handleSelectWorkspace,
  selectedWorkspace,
}) {
  return (
    <section className="workspace-navigator-card">
      <h4>Subjects & Workspaces</h4>

      <form onSubmit={handleCreateWorkspace} className="create-ws-form">
        <input
          type="text"
          placeholder="New Subject (e.g. Operating Systems)"
          value={form.workspaceName}
          onChange={(e) =>
            updateField("workspaceName", e.target.value)
          }
          required
        />
        <button type="submit" className="create-btn">+</button>
      </form>

      <ul className="workspace-list">
        {workspaces.map((ws) => {
          const isSelected = selectedWorkspace && selectedWorkspace.id === ws.id;
          return (
            <li key={ws.id} className="workspace-item">
              <button
                type="button"
                className={`workspace-select-btn ${isSelected ? "active" : ""}`}
                onClick={() => handleSelectWorkspace(ws)}
              >
                <span className="ws-icon">📖</span>
                <span className="ws-name-text">{ws.name}</span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}