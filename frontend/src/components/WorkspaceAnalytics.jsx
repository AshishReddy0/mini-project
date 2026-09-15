import React from "react";
import { ArrowLeft, User, LogOut, Award, Layers, Trash2, ArrowRight, BookOpen, CheckCircle2 } from "lucide-react";

export default function WorkspaceAnalytics({
  user,
  workspaces = [],
  selectedWorkspace,
  onSelectWorkspace,
  onDeleteWorkspace,
  onBack,
  onLogout,
}) {
  // Compute overall account statistics
  const totalWorkspaces = workspaces.length;
  const overallTotalConcepts = workspaces.reduce((acc, ws) => acc + (ws.total_concepts || 0), 0);
  const overallMasteredConcepts = workspaces.reduce((acc, ws) => acc + (ws.mastered_concepts || 0), 0);
  const overallPercentage = overallTotalConcepts > 0 ? Math.round((overallMasteredConcepts / overallTotalConcepts) * 100) : 0;

  return (
    <div className="profile-page-container" style={{ padding: "32px 48px", maxWidth: 960, margin: "0 auto", height: "100%", overflowY: "auto" }}>
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 24 }}>
        <button
          className="secondary-btn"
          style={{ display: "inline-flex", alignItems: "center", gap: 6, cursor: "pointer" }}
          onClick={onBack}
        >
          <ArrowLeft size={16} /> Back to Dashboard
        </button>

        {onLogout && (
          <button
            className="action-btn secondary"
            style={{ color: "#ef4444", display: "inline-flex", alignItems: "center", gap: 6 }}
            onClick={onLogout}
          >
            <LogOut size={15} /> Log out
          </button>
        )}
      </div>

      {/* User Header Profile Card */}
      <div className="profile-user-card" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 16, padding: 24, marginBottom: 24, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.2))", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center", border: "1px solid var(--border-color)" }}>
            <User size={28} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: "1.4rem", color: "var(--text-main)", fontWeight: 700 }}>{user?.name || "Student Profile"}</h2>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)" }}>{user?.email}</span>
          </div>
        </div>

        <div style={{ display: "flex", gap: 20, textAlign: "right" }}>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Workspaces</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--text-main)" }}>{totalWorkspaces}</div>
          </div>
          <div>
            <div style={{ fontSize: "0.75rem", color: "var(--text-muted)", textTransform: "uppercase", fontWeight: 700 }}>Concepts Mastered</div>
            <div style={{ fontSize: "1.5rem", fontWeight: 800, color: "var(--success)" }}>{overallMasteredConcepts} / {overallTotalConcepts}</div>
          </div>
        </div>
      </div>

      {/* Account Overall Mastery Summary Banner */}
      <div className="profile-mastery-card" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 16, padding: 24, marginBottom: 32 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
          <div>
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 700 }}>
              Overall Syllabus Progress
            </span>
            <h1 style={{ margin: "2px 0 0 0", fontSize: "2.2rem", color: "var(--accent)", fontWeight: 800 }}>
              {overallPercentage}% <span style={{ fontSize: "1rem", color: "var(--text-muted)", fontWeight: 500 }}>Completed Across All Subjects</span>
            </h1>
          </div>
          <Award size={44} style={{ color: "#f59e0b", opacity: 0.9 }} />
        </div>

        <div className="progress-bar-container" style={{ height: 10, borderRadius: 6, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
          <div
            className="progress-bar-fill"
            style={{
              width: `${overallPercentage}%`,
              height: "100%",
              background: "linear-gradient(90deg, #6366f1, #10b981)",
              borderRadius: 6,
              transition: "width 0.5s ease"
            }}
          />
        </div>
      </div>

      {/* Workspaces List Section */}
      <div className="profile-workspaces-section">
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: "1.15rem", fontWeight: 700, color: "var(--text-main)", display: "flex", alignItems: "center", gap: 8 }}>
            <Layers size={18} style={{ color: "var(--accent)" }} />
            All Workspaces ({workspaces.length})
          </h3>
        </div>

        {workspaces.length === 0 ? (
          <div className="card" style={{ padding: 32, textAlign: "center", color: "var(--text-muted)" }}>
            No workspaces found. Create one from the landing screen to start studying!
          </div>
        ) : (
          <div className="profile-workspaces-grid" style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            {workspaces.map((ws) => {
              const total = ws.total_concepts || 0;
              const mastered = ws.mastered_concepts || 0;
              const pct = total > 0 ? Math.round((mastered / total) * 100) : 0;
              const isCurrent = selectedWorkspace?.id === ws.id;

              return (
                <div
                  key={ws.id}
                  className="profile-workspace-row"
                  style={{
                    background: "var(--bg-card)",
                    border: `1.5px solid ${isCurrent ? "var(--accent)" : "var(--border-color)"}`,
                    borderRadius: 14,
                    padding: "18px 22px",
                    display: "flex",
                    alignItems: "center",
                    justify: "space-between",
                    gap: 16,
                    transition: "all 0.2s ease"
                  }}
                >
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 6 }}>
                      <div style={{ width: 34, height: 34, borderRadius: 8, background: "rgba(99,102,241,0.12)", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <BookOpen size={18} />
                      </div>
                      <div>
                        <span style={{ fontSize: "1rem", fontWeight: 700, color: "var(--text-main)" }}>
                          {ws.name}
                        </span>
                        {isCurrent && (
                          <span style={{ marginLeft: 8, fontSize: "0.68rem", fontWeight: 700, padding: "2px 6px", borderRadius: 4, background: "rgba(99,102,241,0.2)", color: "var(--accent)" }}>
                            Active
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Progress Bar & Concepts Done Counter */}
                    <div style={{ display: "flex", alignItems: "center", gap: 14, marginTop: 8 }}>
                      <div style={{ flex: 1, height: 7, borderRadius: 4, background: "rgba(255,255,255,0.08)", overflow: "hidden" }}>
                        <div
                          style={{
                            width: `${pct}%`,
                            height: "100%",
                            background: "linear-gradient(90deg, #6366f1, #10b981)",
                            borderRadius: 4
                          }}
                        />
                      </div>
                      <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "var(--text-main)", whiteSpace: "nowrap" }}>
                        Concepts Done: <span style={{ color: "var(--accent)" }}>{mastered} / {total}</span> ({pct}%)
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div style={{ display: "flex", alignItems: "center", gap: 8, flexShrink: 0 }}>
                    <button
                      className="action-btn primary"
                      style={{ fontSize: "0.8rem", padding: "8px 14px", display: "inline-flex", alignItems: "center", gap: 4 }}
                      onClick={() => onSelectWorkspace && onSelectWorkspace(ws)}
                    >
                      Open <ArrowRight size={13} />
                    </button>

                    {onDeleteWorkspace && (
                      <button
                        className="action-btn secondary"
                        style={{ padding: "8px 10px", color: "#ef4444", borderColor: "rgba(239,68,68,0.3)", background: "rgba(239,68,68,0.1)" }}
                        onClick={() => onDeleteWorkspace(ws.id, ws.name)}
                        title="Delete Workspace"
                      >
                        <Trash2 size={15} />
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
