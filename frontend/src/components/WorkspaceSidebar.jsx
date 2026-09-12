import React, { useRef } from "react";
import { ArrowLeft, Plus, Trash2, LogOut, FileText, FileImage, FileCode, FileUp, Download } from "lucide-react";

function getFileIcon(filename) {
  const ext = filename?.split(".").pop()?.toLowerCase() || "";
  const size = 14;
  if (ext === "pdf" || ext === "txt") {
    return <FileText size={size} />;
  }
  if (["png", "jpg", "jpeg"].includes(ext)) {
    return <FileImage size={size} />;
  }
  if (["doc", "docx"].includes(ext)) {
    return <FileCode size={size} />;
  }
  return <FileText size={size} />;
}

export default function WorkspaceSidebar({
  workspace,
  documents,
  activeDocId,
  onBackClick,
  onFileClick,
  onAddFile,
  onDeleteFile,
  onLogout,
}) {
  const fileInputRef = useRef(null);

  const handleAddClick = () => fileInputRef.current?.click();

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) onAddFile(file);
    e.target.value = "";
  };

  const handleDownloadFile = (e, doc) => {
    e.stopPropagation();
    if (!doc?.file_path) return;
    const fileUrl = `http://127.0.0.1:8000/${doc.file_path.replace(/\\/g, "/")}`;
    const a = document.createElement("a");
    a.href = fileUrl;
    a.download = doc.filename;
    a.target = "_blank";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <aside className="workspace-sidebar">
      {/* Top bar — back button + workspace name */}
      <div className="sidebar-topbar">
        <button className="back-btn" onClick={onBackClick} title="All Workspaces">
          <ArrowLeft size={16} />
        </button>
        <span className="sidebar-workspace-name">{workspace.name}</span>
      </div>

      <span className="sidebar-section-label">Materials</span>

      {/* File list */}
      <div className="sidebar-files-list">
        {documents.length === 0 ? (
          <div style={{ padding: "14px 10px", fontSize: "0.78rem", color: "var(--text-muted)", textAlign: "center" }}>
            No files yet.<br />Add your first file below.
          </div>
        ) : (
          documents.map((doc) => (
            <div
              key={doc.id}
              className={`sidebar-file-item ${activeDocId === doc.id ? "active" : ""}`}
              onClick={() => onFileClick(doc)}
            >
              <span className="file-icon" style={{ display: "flex", alignItems: "center" }}>
                {getFileIcon(doc.filename)}
              </span>
              <span className="file-name" title={doc.filename}>{doc.filename}</span>
              <div className="file-actions" style={{ display: "flex", gap: 4, alignItems: "center" }}>
                <button
                  className="file-delete-btn"
                  style={{ display: "flex", alignItems: "center" }}
                  onClick={(e) => handleDownloadFile(e, doc)}
                  title="Download file"
                >
                  <Download size={12} />
                </button>
                <button
                  className="file-delete-btn"
                  style={{ display: "flex", alignItems: "center" }}
                  onClick={(e) => { e.stopPropagation(); onDeleteFile(doc.id); }}
                  title="Remove file"
                >
                  <Trash2 size={12} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Add File Button */}
      <div className="sidebar-add-file">
        <button className="add-file-btn" onClick={handleAddClick}>
          <FileUp size={14} /> Add File
        </button>
        <input
          ref={fileInputRef}
          type="file"
          style={{ display: "none" }}
          accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg"
          onChange={handleFileChange}
        />
      </div>

      {/* Footer — logout */}
      <div className="sidebar-footer">
        <button className="logout-btn" style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }} onClick={onLogout}>
          <LogOut size={13} /> Log out
        </button>
      </div>
    </aside>
  );
}
