import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Map, RefreshCw, ChevronLeft, ChevronRight, Loader2, FileText, Paperclip, X, Lock, PlayCircle, CheckCircle, ChevronDown, ChevronUp } from "lucide-react";

const ANSWER_FORMAT_OPTIONS = [
  { id: "meaning", label: "Meaning / Definition" },
  { id: "types", label: "Types" },
  { id: "types_meaning", label: "Types + Meaning" },
  { id: "application", label: "Real-world Application" },
  { id: "working", label: "How it Works / Process" },
  { id: "comparison", label: "Comparison / Difference" },
  { id: "advantages", label: "Advantages & Disadvantages" },
  { id: "examples", label: "Examples" },
];

const ALLOWED_EXTENSIONS = ["pdf", "doc", "docx", "txt"];

function getExt(filename) {
  return filename?.split(".").pop()?.toLowerCase() || "";
}

export default function AnimatedRoadmap({
  workspaceId,
  documents,
  activeNodeId,
  onNodeClick,
  expanded,
  onToggleExpand,
  roadmapConfig,
  onRoadmapConfigured,
  onMasteriesUpdate,
}) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [expandedNodeId, setExpandedNodeId] = useState(null);
  const [currentNodeIndex, setCurrentNodeIndex] = useState(0);

  const [setupStep, setSetupStep] = useState("file");
  const [portionDocId, setPortionDocId] = useState("");
  const [portionText, setPortionText] = useState("");
  const [portionFile, setPortionFile] = useState(null);
  const [portionFileError, setPortionFileError] = useState("");
  const [selectedFormats, setSelectedFormats] = useState([]);
  const [customFormat, setCustomFormat] = useState("");

  const fileInputRef = useRef(null);

  useEffect(() => {
    if (workspaceId && roadmapConfig) loadGraph();
  }, [workspaceId]);

  const loadGraph = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await api.getGraph(workspaceId);
      if (data?.nodes?.length > 0) {
        setGraphData(data);
        if (onMasteriesUpdate && data.masteries) onMasteriesUpdate(data.masteries);
        setSetupStep("done");
      } else {
        setGraphData(null);
      }
    } catch (_) {
      setGraphData(null);
    } finally {
      setLoading(false);
    }
  };

  const handlePortionFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const ext = getExt(file.name);
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setPortionFileError(`❌ "${file.name}" is not supported. Please upload a PDF, DOC, DOCX, or TXT file.`);
      setPortionFile(null);
      e.target.value = "";
      return;
    }
    setPortionFileError("");
    setPortionFile(file);
  };

  const handlePortionNext = () => {
    const hasFile = portionFile || portionDocId || portionText.trim();
    if (!hasFile) {
      setPortionFileError("Please upload a file, select an existing material, or paste your portion text.");
      return;
    }
    setPortionFileError("");
    setSetupStep("format");
  };

  const handleFormatConfirm = async () => {
    const config = {
      portionDocId: portionDocId || null,
      portionText: portionText.trim() || null,
      portionFile: portionFile || null,
      formats: selectedFormats,
      customFormat: customFormat.trim() || null,
    };

    onRoadmapConfigured(config);

    let uploadedDocId = portionDocId || null;
    if (portionFile) {
      try {
        setGenerating(true);
        const res = await api.uploadDocument(workspaceId, portionFile);
        uploadedDocId = res.id;
      } catch (err) {
        setError(`Upload failed: ${err.message}`);
        setGenerating(false);
        return;
      }
    }

    setGenerating(true);
    setError("");
    try {
      await api.generateGraph(workspaceId, {
        document_id: uploadedDocId || null,
        answer_formats: selectedFormats,
        custom_format: customFormat.trim() || null,
        portion_text: portionText.trim() || null,
      });
      await loadGraph();
      setSetupStep("done");
    } catch (err) {
      setError(err.message || "Failed to generate roadmap");
    } finally {
      setGenerating(false);
    }
  };

  const toggleFormat = (id) => {
    setSelectedFormats((prev) =>
      prev.includes(id) ? prev.filter((f) => f !== id) : [...prev, id]
    );
  };

  const orderedNodes = graphData?.nodes
    ? [...graphData.nodes].sort((a, b) => (a.order_hint ?? 0) - (b.order_hint ?? 0))
    : [];

  const masteredCount = orderedNodes.filter(
    (n) => graphData?.masteries?.[n.id]?.status === "mastered"
  ).length;
  const progress = orderedNodes.length > 0 ? masteredCount / orderedNodes.length : 0;

  const getMasteryStatus = (nodeId) =>
    graphData?.masteries?.[nodeId]?.status || "locked";

  const isConnectorFilled = (index) => {
    if (index === 0) return false;
    return getMasteryStatus(orderedNodes[index - 1].id) === "mastered";
  };

  const handleNodeClick = (node, index) => {
    const status = getMasteryStatus(node.id);
    if (status === "locked") return;
    setCurrentNodeIndex(index);
    setExpandedNodeId((prev) => (prev === node.id ? null : node.id));
    onNodeClick(node, graphData?.masteries);
  };

  const goPrev = () => {
    const idx = Math.max(0, currentNodeIndex - 1);
    setCurrentNodeIndex(idx);
    const node = orderedNodes[idx];
    if (node) {
      setExpandedNodeId(node.id);
      onNodeClick(node, graphData?.masteries);
    }
  };

  const goNext = () => {
    const idx = Math.min(orderedNodes.length - 1, currentNodeIndex + 1);
    setCurrentNodeIndex(idx);
    const node = orderedNodes[idx];
    if (node) {
      setExpandedNodeId(node.id);
      onNodeClick(node, graphData?.masteries);
    }
  };

  const handleRebuild = () => {
    setSetupStep("file");
    setPortionDocId("");
    setPortionText("");
    setPortionFile(null);
    setPortionFileError("");
    setSelectedFormats([]);
    setCustomFormat("");
    setGraphData(null);
    onRoadmapConfigured(null);
  };

  if (!expanded) {
    return (
      <div className="roadmap-panel roadmap-panel-collapsed" onClick={onToggleExpand} title="Open Prep Roadmap">
        <div className="roadmap-collapsed-label">
          <Map size={16} />
          <span className="roadmap-collapsed-text">Roadmap</span>
          {graphData && orderedNodes.length > 0 && (
            <span className="roadmap-mini-progress">{masteredCount}/{orderedNodes.length}</span>
          )}
          <ChevronLeft size={16} className="roadmap-expand-arrow" />
        </div>
      </div>
    );
  }

  return (
    <div className="roadmap-panel">
      <div className="roadmap-header">
        <div className="roadmap-title-row">
          <span className="roadmap-title" style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Map size={14} style={{ color: "var(--accent)" }} /> Prep Roadmap
          </span>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            {setupStep === "done" && (
              <button className="roadmap-rebuild-btn" onClick={handleRebuild} title="Re-configure roadmap">
                <RefreshCw size={10} /> Reset
              </button>
            )}
            <button className="roadmap-rebuild-btn" onClick={onToggleExpand} title="Collapse">
              <ChevronRight size={12} />
            </button>
          </div>
        </div>

        {setupStep === "done" && graphData && orderedNodes.length > 0 && (
          <div className="roadmap-progress-bar-wrap">
            <div className="roadmap-progress-track">
              <div className="roadmap-progress-fill" style={{ width: `${Math.round(progress * 100)}%` }} />
            </div>
            <span className="roadmap-progress-label">{masteredCount}/{orderedNodes.length}</span>
          </div>
        )}
      </div>

      <div className="roadmap-scroll-area">
        {setupStep === "file" && (
          <div className="roadmap-setup-panel">
            <div className="setup-step-title">
              <span className="setup-step-num">1</span>
              <span>Select your study portion</span>
            </div>
            <p className="setup-hint">
              Choose an existing file or upload your specific portion/syllabus/Q-bank.
            </p>

            {documents.length > 0 && (
              <div className="setup-field">
                <label className="setup-label">From uploaded materials</label>
                <select
                  className="setup-select"
                  value={portionDocId}
                  onChange={(e) => setPortionDocId(e.target.value)}
                >
                  <option value="">— Pick a file (optional) —</option>
                  {documents.map((d) => (
                    <option key={d.id} value={d.id}>{d.filename}</option>
                  ))}
                </select>
              </div>
            )}

            <div className="setup-field">
              <label className="setup-label">Upload new portion file</label>
              <div
                className={`setup-drop-zone ${portionFile ? "has-file" : ""}`}
                onClick={() => fileInputRef.current?.click()}
              >
                {portionFile ? (
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <FileText size={14} /> {portionFile.name}{" "}
                    <button className="drop-clear-btn" style={{ display: "inline-flex", padding: 2 }} onClick={(e) => { e.stopPropagation(); setPortionFile(null); }}>
                      <X size={12} />
                    </button>
                  </span>
                ) : (
                  <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                    <Paperclip size={14} /> Click to upload PDF, DOC, DOCX, TXT
                  </span>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                style={{ display: "none" }}
                onChange={handlePortionFileChange}
              />
              {portionFileError && (
                <div className="setup-file-error">{portionFileError}</div>
              )}
            </div>

            <div className="setup-field">
              <label className="setup-label">Or paste syllabus / portion text</label>
              <textarea
                className="setup-textarea"
                rows={4}
                placeholder="Paste topic list, chapter names, or any text describing the portion..."
                value={portionText}
                onChange={(e) => setPortionText(e.target.value)}
              />
            </div>

            <button className="generate-roadmap-btn" onClick={handlePortionNext} style={{ width: "100%" }}>
              Next: Configure Format →
            </button>
          </div>
        )}

        {setupStep === "format" && (
          <div className="roadmap-setup-panel">
            <div className="setup-step-title">
              <span className="setup-step-num">2</span>
              <span>Answer format & style</span>
            </div>
            <p className="setup-hint">
              Choose what each concept answer should cover. Selected formats apply to the entire roadmap.
            </p>

            <div className="format-options-grid">
              {ANSWER_FORMAT_OPTIONS.map((opt) => (
                <div
                  key={opt.id}
                  className={`format-option-chip ${selectedFormats.includes(opt.id) ? "selected" : ""}`}
                  onClick={() => toggleFormat(opt.id)}
                >
                  {opt.label}
                </div>
              ))}
            </div>

            <div className="setup-field" style={{ marginTop: 14 }}>
              <label className="setup-label">Custom format instructions (optional)</label>
              <textarea
                className="setup-textarea"
                rows={3}
                placeholder="e.g. Always include a diagram description. Give analogies..."
                value={customFormat}
                onChange={(e) => setCustomFormat(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              <button className="secondary-btn" onClick={() => setSetupStep("file")}>← Back</button>
              <button
                className="generate-roadmap-btn"
                onClick={handleFormatConfirm}
                disabled={generating}
                style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
              >
                {generating ? <Loader2 size={14} className="loading-spinner-animate" style={{ animation: "spin 1s linear infinite" }} /> : "Generate Roadmap"}
              </button>
            </div>
            {error && <div className="setup-file-error" style={{ marginTop: 8 }}>{error}</div>}
          </div>
        )}

        {setupStep === "done" && (
          <>
            {error && <div className="error-banner">{error}</div>}
            {loading || generating ? (
              <div className="roadmap-empty">
                <Loader2 size={24} className="loading-spinner-animate" style={{ animation: "spin 1s linear infinite" }} />
                <p>{generating ? "Analyzing materials…" : "Loading…"}</p>
              </div>
            ) : !graphData ? (
              <div className="roadmap-empty">
                <Map size={28} style={{ opacity: 0.5 }} />
                <h4>No Roadmap Yet</h4>
                <button className="generate-roadmap-btn" onClick={handleRebuild}>Configure &amp; Generate</button>
              </div>
            ) : (
              <>
                {orderedNodes.map((node, index) => {
                  const status = getMasteryStatus(node.id);
                  const isActive = activeNodeId === node.id;
                  const isExpanded = expandedNodeId === node.id;
                  const subPoints = node.sub_points || [];

                  return (
                    <div key={node.id} className="roadmap-node-wrapper">
                      {index > 0 && (
                        <div className={`roadmap-connector-line ${isConnectorFilled(index) ? "mastered" : ""}`} />
                      )}
                      <div
                        className={`roadmap-node-card ${status} ${isActive ? "active" : ""}`}
                        onClick={() => handleNodeClick(node, index)}
                        title={status === "locked" ? "Complete prerequisites first" : `Open: ${node.title}`}
                      >
                        <div className="node-status-circle" style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                          {status === "mastered" ? (
                            <CheckCircle size={14} style={{ color: "var(--success)" }} />
                          ) : status === "unlocked" ? (
                            <PlayCircle size={14} style={{ color: "var(--primary)" }} />
                          ) : (
                            <Lock size={12} style={{ color: "var(--text-muted)" }} />
                          )}
                        </div>
                        <div className="node-card-body">
                          <div className="node-card-title">{node.title}</div>
                          <div className="node-card-sub" style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                            <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
                              <span>{node.difficulty || "medium"}</span>
                              {subPoints.length > 0 && (
                                <span className="sub-count-badge">{subPoints.length} topics</span>
                              )}
                            </div>
                            {subPoints.length > 0 && (
                              <div style={{ color: "var(--text-muted)", display: "flex" }}>
                                {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                              </div>
                            )}
                          </div>
                          {isExpanded && subPoints.length > 0 && (
                            <div className="node-sub-points-expanded">
                              {subPoints.map((sp, i) => (
                                <div key={i} className="node-sub-point-item">
                                  <strong>{sp.title}</strong>
                                  {sp.description}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </>
            )}
          </>
        )}
      </div>

      {setupStep === "done" && graphData && orderedNodes.length > 0 && (
        <div className="roadmap-nav-bar">
          <button
            className="roadmap-nav-btn prev"
            onClick={goPrev}
            disabled={currentNodeIndex === 0}
            title="Previous concept"
          >
            ← Prev
          </button>

          <div className="roadmap-nav-indicator">
            <span className="nav-node-label">
              {orderedNodes[currentNodeIndex]?.title?.substring(0, 20) || "—"}
              {(orderedNodes[currentNodeIndex]?.title?.length || 0) > 20 ? "…" : ""}
            </span>
            <span className="nav-node-index">{currentNodeIndex + 1} / {orderedNodes.length}</span>
          </div>

          <button
            className="roadmap-nav-btn next"
            onClick={goNext}
            disabled={currentNodeIndex === orderedNodes.length - 1}
            title="Next concept"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
}
