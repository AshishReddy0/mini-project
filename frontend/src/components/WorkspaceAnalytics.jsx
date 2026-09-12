import React from "react";
import { ArrowLeft, User, LogOut, Award } from "lucide-react";

export default function WorkspaceAnalytics({
  user,
  workspace,
  graphNodes = [],
  masteries = {},
  onBack,
  onLogout,
}) {
  const totalNodes = graphNodes.length;
  const masteredCount = Object.values(masteries || {}).filter((m) => m?.status === "mastered").length;
  const masteryPercentage = totalNodes > 0 ? Math.round((masteredCount / totalNodes) * 100) : 0;

  return (
    <div className="profile-page-container" style={{ padding: "40px 60px", maxWidth: 800, margin: "0 auto", height: "100%", overflowY: "auto" }}>
      <button
        className="secondary-btn"
        style={{ display: "inline-flex", alignItems: "center", gap: 6, marginBottom: 24, cursor: "pointer" }}
        onClick={onBack}
      >
        <ArrowLeft size={16} /> Back to Workspace
      </button>

      <div className="profile-user-card" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 16, padding: 28, marginBottom: 28, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 56, height: 56, borderRadius: "50%", background: "rgba(99,102,241,0.15)", color: "var(--accent)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <User size={28} />
          </div>
          <div>
            <h2 style={{ margin: 0, fontSize: "1.4rem", color: "var(--text-main)", fontWeight: 700 }}>{user?.name || "Student Profile"}</h2>
            <span style={{ fontSize: "0.9rem", color: "var(--text-muted)" }}>{user?.email}</span>
          </div>
        </div>

        {onLogout && (
          <button
            className="action-btn secondary"
            style={{ color: "#ef4444", display: "inline-flex", alignItems: "center", gap: 6 }}
            onClick={onLogout}
          >
            <LogOut size={16} /> Log out
          </button>
        )}
      </div>

      <div className="profile-mastery-card" style={{ background: "var(--bg-card)", border: "1px solid var(--border-color)", borderRadius: 16, padding: 28 }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
          <div>
            <span style={{ fontSize: "0.85rem", color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.5px", fontWeight: 600 }}>
              {workspace?.name ? `${workspace.name} Mastery` : "Overall Concept Mastery"}
            </span>
            <h1 style={{ margin: "4px 0 0 0", fontSize: "2.4rem", color: "var(--accent)", fontWeight: 800 }}>
              {masteryPercentage}%
            </h1>
          </div>
          <Award size={48} style={{ color: "#f59e0b", opacity: 0.9 }} />
        </div>

        <div className="progress-bar-container" style={{ height: 12, borderRadius: 6, background: "rgba(255,255,255,0.08)", overflow: "hidden", marginBottom: 12 }}>
          <div
            className="progress-bar-fill"
            style={{
              width: `${masteryPercentage}%`,
              height: "100%",
              background: "linear-gradient(90deg, var(--primary), var(--accent))",
              borderRadius: 6,
              transition: "width 0.5s ease"
            }}
          />
        </div>

        <div style={{ fontSize: "0.95rem", color: "var(--text-main)", fontWeight: 600 }}>
          Concepts Done: {masteredCount} / {totalNodes}
        </div>
      </div>
    </div>
  );
}
