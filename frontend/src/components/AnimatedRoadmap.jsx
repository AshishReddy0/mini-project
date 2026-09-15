import React, { useEffect, useRef, useState } from "react";
import { api } from "../api";
import { Map, RefreshCw, ChevronLeft, ChevronRight, Loader2, FileText, Paperclip, X, Lock, PlayCircle, CheckCircle, ChevronDown, ChevronUp, Trash2 } from "lucide-react";

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
  onDocumentsUpdated,
  masteries,
}) {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
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
    if (workspaceId) loadGraph();
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
    } catch (err) {
      setError(err.message || "Failed to load concept graph.");
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

  const [filterMode, setFilterMode] = useState("all"); // 'all' | 'undone' | 'mastered'
  const [groupByUnit, setGroupByUnit] = useState(false);

  const handlePortionSubmit = async () => {
    const hasFile = portionFile || portionDocId || portionText.trim();
    if (!hasFile) {
      setPortionFileError("Please upload a file, select an existing material, or paste your portion text.");
      return;
    }
    setPortionFileError("");

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
        portion_text: portionText.trim() || null,
      });
      await loadGraph();
      if (onDocumentsUpdated) {
        await onDocumentsUpdated();
      }
      setSetupStep("done");
      setPortionFile(null);
      setPortionText("");
      setPortionDocId("");
    } catch (err) {
      setError(err.message || "Failed to generate concepts");
    } finally {
      setGenerating(false);
    }
  };

  const handleClearGraph = async () => {
    if (!window.confirm("Are you sure you want to clear all concepts from this syllabus?")) return;
    setLoading(true);
    setError("");
    try {
      await api.clearGraph(workspaceId);
      setGraphData(null);
      setSetupStep("file");
    } catch (err) {
      setError(err.message || "Failed to clear concept syllabus.");
    } finally {
      setLoading(false);
    }
  };

  const handleExportPDF = async () => {
    setExportingPdf(true);
    setError("");
    try {
      await api.downloadSyllabusPDF(workspaceId, "Concept_Syllabus.pdf");
    } catch (err) {
      setError("Failed to export PDF: " + err.message);
    } finally {
      setExportingPdf(false);
    }
  };

  const [selectedUnitTab, setSelectedUnitTab] = useState("all");

  const orderedNodes = graphData?.nodes
    ? [...graphData.nodes].sort((a, b) => (a.order_hint ?? 0) - (b.order_hint ?? 0))
    : [];

  const ROMAN_MAP = { i: 1, ii: 2, iii: 3, iv: 4, v: 5, vi: 6, vii: 7, viii: 8, ix: 9, x: 10 };

  function getSingleUnits(unitRef) {
    if (!unitRef) return ["Unit 1"];
    const parts = String(unitRef).split(/[,&]|\band\b/i).map((s) => s.trim()).filter(Boolean);
    const cleaned = parts.map((p) => {
      // 1. Match Roman numeral unit (e.g. UNIT-I, UNIT-II, Unit III, UNIT-IV, UNIT-V)
      const romanMatch = p.match(/(?:unit|module|chapter)?\s*[\:\-]?\s*\b([ivx]+)\b/i);
      if (romanMatch && romanMatch[1]) {
        const val = ROMAN_MAP[romanMatch[1].toLowerCase()];
        if (val) return `Unit ${val}`;
      }

      // 2. Match numeric unit (e.g. Unit 1, Unit-1, Module 2, Chapter 3)
      const numMatch = p.match(/(?:unit|module|chapter)?\s*[\:\-]?\s*(\d+)/i);
      if (numMatch && numMatch[1]) {
        return `Unit ${parseInt(numMatch[1], 10)}`;
      }

      if (ROMAN_MAP[p.toLowerCase()]) {
        return `Unit ${ROMAN_MAP[p.toLowerCase()]}`;
      }

      const stripped = p.replace(/[:].*$/, "").trim();
      if (!stripped || ["UNIT", "MODULE", "CHAPTER"].includes(stripped.toUpperCase())) {
        return "Unit 1";
      }
      return stripped;
    }).filter(Boolean);
    return Array.from(new Set(cleaned));
  }

  const availableUnits = Array.from(
    new Set(orderedNodes.flatMap((n) => getSingleUnits(n.unit_ref)))
  ).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, "")) || 0;
    const numB = parseInt(b.replace(/\D/g, "")) || 0;
    return numA - numB || a.localeCompare(b);
  });

  const unitNodeCounts = {};
  orderedNodes.forEach((node) => {
    const nodeUnits = getSingleUnits(node.unit_ref);
    nodeUnits.forEach((u) => {
      unitNodeCounts[u] = (unitNodeCounts[u] || 0) + 1;
    });
  });

  const getMasteryStatus = (nodeId) =>
    masteries?.[nodeId]?.status || graphData?.masteries?.[nodeId]?.status || "locked";

  const filteredNodes = orderedNodes.filter((node) => {
    const status = getMasteryStatus(node.id);
    if (filterMode === "undone" && status === "mastered") return false;
    if (filterMode === "mastered" && status !== "mastered") return false;
    if (selectedUnitTab !== "all") {
      const nodeUnits = getSingleUnits(node.unit_ref);
      if (!nodeUnits.includes(selectedUnitTab)) return false;
    }
    return true;
  });

  // Group nodes strictly Unit-Wise (Unit 1, Unit 2, Unit 3...)
  const unitGroups = {};
  filteredNodes.forEach((node) => {
    const units = getSingleUnits(node.unit_ref);
    const primaryUnit = units[0] || "Unit 1";
    if (!unitGroups[primaryUnit]) unitGroups[primaryUnit] = [];
    unitGroups[primaryUnit].push(node);
  });

  const sortedUnitKeys = Object.keys(unitGroups).sort((a, b) => {
    const numA = parseInt(a.replace(/\D/g, "")) || 0;
    const numB = parseInt(b.replace(/\D/g, "")) || 0;
    return numA - numB || a.localeCompare(b);
  });

  const masteredCount = orderedNodes.filter(
    (n) => getMasteryStatus(n.id) === "mastered"
  ).length;

  const handleNodeClick = (node, index) => {
    setCurrentNodeIndex(index);
    onNodeClick(node, masteries || graphData?.masteries);
  };

  const goPrev = () => {
    const idx = Math.max(0, currentNodeIndex - 1);
    setCurrentNodeIndex(idx);
    const node = filteredNodes[idx];
    if (node) {
      onNodeClick(node, masteries || graphData?.masteries);
    }
  };

  const goNext = () => {
    const idx = Math.min(filteredNodes.length - 1, currentNodeIndex + 1);
    setCurrentNodeIndex(idx);
    const node = filteredNodes[idx];
    if (node) {
      onNodeClick(node, masteries || graphData?.masteries);
    }
  };

  if (!expanded) {
    return (
      <div className="roadmap-panel roadmap-panel-collapsed" onClick={onToggleExpand} title="Open Concept Syllabus">
        <div className="roadmap-collapsed-label">
          <Map size={16} />
          <span className="roadmap-collapsed-text">Concept Syllabus</span>
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
            <Map size={14} style={{ color: "var(--accent)" }} /> Concept Syllabus
          </span>
          <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
            {setupStep === "done" && (
              <>
                <button className="roadmap-rebuild-btn" onClick={() => setSetupStep("file")} title="Add more portion/material">
                  + Feed Portion
                </button>
                <button
                  className="roadmap-rebuild-btn"
                  onClick={handleExportPDF}
                  disabled={exportingPdf}
                  title="Export Concept Syllabus PDF Report"
                  style={{ display: "flex", alignItems: "center", gap: 4, background: "rgba(16,185,129,0.15)", color: "#10b981", border: "1px solid rgba(16,185,129,0.3)" }}
                >
                  {exportingPdf ? (
                    <Loader2 size={12} className="loading-spinner-animate" style={{ animation: "spin 1s linear infinite" }} />
                  ) : (
                    <FileText size={12} />
                  )}
                  Export PDF
                </button>
                <button
                  className="roadmap-rebuild-btn"
                  onClick={handleClearGraph}
                  title="Clear concept syllabus feed"
                  style={{ color: "var(--error)", display: "flex", alignItems: "center", justifyContent: "center", padding: "4px 7px" }}
                >
                  <Trash2 size={13} />
                </button>
              </>
            )}
            <button className="roadmap-rebuild-btn" onClick={onToggleExpand} title="Collapse">
              <ChevronRight size={12} />
            </button>
          </div>
        </div>

        {setupStep === "done" && graphData && orderedNodes.length > 0 && (
          <>
            {/* Horizontal Unit Tabs Bar */}
            {availableUnits.length > 0 && (
              <div className="unit-tabs-bar">
                <button
                  className={`duration-chip ${selectedUnitTab === "all" ? "active" : ""}`}
                  style={{
                    fontSize: "0.7rem",
                    padding: "3px 8px",
                    borderRadius: "4px",
                    border: "1px solid var(--border-color)",
                    background: selectedUnitTab === "all" ? "var(--primary)" : "var(--bg-card)",
                    color: selectedUnitTab === "all" ? "white" : "var(--text-muted)",
                    whiteSpace: "nowrap",
                    cursor: "pointer"
                  }}
                  onClick={() => setSelectedUnitTab("all")}
                >
                  All Units ({orderedNodes.length})
                </button>

                {availableUnits.map((unit) => (
                  <button
                    key={unit}
                    className={`duration-chip ${selectedUnitTab === unit ? "active" : ""}`}
                    style={{
                      fontSize: "0.7rem",
                      padding: "3px 8px",
                      borderRadius: "4px",
                      border: "1px solid var(--border-color)",
                      background: selectedUnitTab === unit ? "var(--primary)" : "var(--bg-card)",
                      color: selectedUnitTab === unit ? "white" : "var(--text-muted)",
                      whiteSpace: "nowrap",
                      cursor: "pointer"
                    }}
                    onClick={() => setSelectedUnitTab(unit)}
                  >
                    📁 {unit} ({unitNodeCounts[unit] || 0})
                  </button>
                ))}
              </div>
            )}

            {/* Filter Controls */}
            <div className="syllabus-filter-bar" style={{ display: "flex", gap: 6, marginTop: 6, alignItems: "center" }}>
              <select
                className="setup-select"
                style={{ padding: "3px 6px", fontSize: "0.72rem", flex: 1 }}
                value={filterMode}
                onChange={(e) => setFilterMode(e.target.value)}
              >
                <option value="all">Show All Concepts</option>
                <option value="undone">Undone Only ({orderedNodes.length - masteredCount})</option>
                <option value="mastered">Mastered Only ({masteredCount})</option>
              </select>
            </div>
          </>
        )}
      </div>

      <div className="roadmap-scroll-area">
        {setupStep === "file" && (
          <div className="roadmap-setup-panel">
            <div className="setup-step-title">
              <span className="setup-step-num">1</span>
              <span>Feed Syllabus / Portion</span>
            </div>
            <p className="setup-hint">
              Upload a specific portion file or paste text to extract and append new unique concepts.
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
                placeholder="Paste topic list, unit names, chapter outlines..."
                value={portionText}
                onChange={(e) => setPortionText(e.target.value)}
              />
            </div>

            <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
              {graphData && (
                <button className="secondary-btn" onClick={() => setSetupStep("done")}>Cancel</button>
              )}
              <button
                className="generate-roadmap-btn"
                onClick={handlePortionSubmit}
                disabled={generating}
                style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", gap: 6 }}
              >
                {generating ? <Loader2 size={14} className="loading-spinner-animate" style={{ animation: "spin 1s linear infinite" }} /> : "Extract & Add Concepts"}
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
                <p>{generating ? "Extracting & adding concepts…" : "Loading…"}</p>
              </div>
            ) : !graphData || orderedNodes.length === 0 ? (
              <div className="roadmap-empty">
                <Map size={28} style={{ opacity: 0.5 }} />
                <h4>No Concepts Yet</h4>
                <button className="generate-roadmap-btn" onClick={() => setSetupStep("file")}>Feed Portion</button>
              </div>
            ) : (
              <>
                {sortedUnitKeys.map((unitKey) => (
                  <div key={unitKey} className="category-section" style={{ marginBottom: 16 }}>
                    <div className="category-header" style={{ fontSize: "0.78rem", fontWeight: 700, color: "var(--accent)", padding: "6px 10px", background: "rgba(99,102,241,0.1)", borderRadius: 6, marginBottom: 8, display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                      <span>📁 {unitKey}</span>
                      <span style={{ fontSize: "0.7rem", opacity: 0.85 }}>{unitGroups[unitKey].length} concepts</span>
                    </div>
                    {unitGroups[unitKey].map((node, index) => renderNodeCard(node, index))}
                  </div>
                ))}
              </>
            )}
          </>
        )}
      </div>

      {setupStep === "done" && graphData && filteredNodes.length > 0 && (
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
              {filteredNodes[currentNodeIndex]?.title?.substring(0, 20) || "—"}
              {(filteredNodes[currentNodeIndex]?.title?.length || 0) > 20 ? "…" : ""}
            </span>
            <span className="nav-node-index">{currentNodeIndex + 1} / {filteredNodes.length}</span>
          </div>

          <button
            className="roadmap-nav-btn next"
            onClick={goNext}
            disabled={currentNodeIndex === filteredNodes.length - 1}
            title="Next concept"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );

  function renderNodeCard(node, index) {
    const status = getMasteryStatus(node.id);
    const isActive = activeNodeId === node.id;
    const subPoints = node.sub_points || [];
    const difficulty = (node.difficulty || "medium").toLowerCase();

    // Map difficulty color styles
    const diffBadgeStyle = {
      easy: { bg: "rgba(16, 185, 129, 0.15)", color: "#10b981", border: "rgba(16, 185, 129, 0.3)" },
      medium: { bg: "rgba(245, 158, 11, 0.15)", color: "#f59e0b", border: "rgba(245, 158, 11, 0.3)" },
      hard: { bg: "rgba(168, 85, 247, 0.15)", color: "#a855f7", border: "rgba(168, 85, 247, 0.3)" },
    }[difficulty] || { bg: "rgba(99, 102, 241, 0.15)", color: "#6366f1", border: "rgba(99, 102, 241, 0.3)" };

    const isMastered = status === "mastered";

    return (
      <div key={node.id} className="roadmap-node-wrapper">
        <div
          className={`roadmap-node-card ${isMastered ? "mastered" : "unmastered"} ${isActive ? "active" : ""}`}
          onClick={() => handleNodeClick(node, index)}
          title={`Click to open reference answer for: ${node.title}`}
        >
          <div className="node-status-circle" style={{ display: "flex", alignItems: "center", justifyContent: "center", marginTop: 2 }}>
            {isMastered ? (
              <CheckCircle size={16} style={{ color: "var(--success)" }} />
            ) : (
              <PlayCircle size={16} style={{ color: isActive ? "var(--accent)" : "var(--primary)" }} />
            )}
          </div>


          <div className="node-card-body" style={{ flex: 1, minWidth: 0 }}>
            {/* Header badges row: Unit Ref & Difficulty */}
            <div style={{ display: "flex", alignItems: "center", gap: 6, flexWrap: "wrap", marginBottom: 4 }}>
              {node.unit_ref && (
                <span className="node-unit-tag" style={{ fontSize: "0.68rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4, background: "rgba(255,255,255,0.07)", color: "var(--text-muted)", border: "1px solid var(--border-color)" }}>
                  {node.unit_ref}
                </span>
              )}
              <span className="node-diff-badge" style={{ fontSize: "0.65rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4, textTransform: "uppercase", background: diffBadgeStyle.bg, color: diffBadgeStyle.color, border: `1px solid ${diffBadgeStyle.border}` }}>
                {difficulty}
              </span>
              {status === "mastered" && (
                <span className="node-mastered-tag" style={{ fontSize: "0.65rem", fontWeight: 700, padding: "1px 6px", borderRadius: 4, background: "rgba(16,185,129,0.2)", color: "#10b981", border: "1px solid rgba(16,185,129,0.4)" }}>
                  ✅ Mastered
                </span>
              )}
            </div>

            {/* Title */}
            <div className="node-card-title" style={{ fontSize: "0.88rem", fontWeight: 700, color: "var(--text-main)", lineHeight: "1.3", marginBottom: 4 }}>
              {node.title}
            </div>

            {/* Summary preview */}
            {node.summary && (
              <div className="node-card-summary" style={{ fontSize: "0.76rem", color: "var(--text-muted)", lineHeight: "1.35", marginBottom: 6, display: "-webkit-box", WebkitLineClamp: 2, WebkitBoxOrient: "vertical", overflow: "hidden" }}>
                {node.summary}
              </div>
            )}

            {/* Sub-points preview chips */}
            {subPoints.length > 0 && (
              <div className="node-subpoints-chips" style={{ display: "flex", gap: 4, flexWrap: "wrap", marginTop: 4 }}>
                {subPoints.slice(0, 3).map((sp, i) => (
                  <span key={i} className="node-subpoint-chip" style={{ fontSize: "0.68rem", padding: "1px 6px", borderRadius: 4, background: "rgba(99,102,241,0.08)", color: "var(--accent)", border: "1px solid rgba(99,102,241,0.18)" }}>
                    • {sp.title || sp}
                  </span>
                ))}
                {subPoints.length > 3 && (
                  <span style={{ fontSize: "0.68rem", color: "var(--text-muted)", alignSelf: "center" }}>
                    +{subPoints.length - 3} more
                  </span>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

}
