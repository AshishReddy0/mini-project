import React, { useEffect, useState, useRef } from "react";
import { api } from "../api";
import MarkdownRenderer from "./MarkdownRenderer";

export default function ConceptGraphPanel({ workspaceId, documents, setActiveNodeContext }) {
  const [graphData, setGraphData] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Node details & Mastery check states
  const [quizData, setQuizData] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [quizScore, setQuizScore] = useState(null);
  const [quizFinished, setQuizFinished] = useState(false);
  
  const [explainText, setExplainText] = useState("");
  const [explainFeedback, setExplainFeedback] = useState(null);
  const [grading, setGrading] = useState(false);
  const [checkMode, setCheckMode] = useState("select"); // select | quiz | explain
  
  const graphContainerRef = useRef(null);

  useEffect(() => {
    loadGraph();
  }, [workspaceId]);

  const loadGraph = async () => {
    setLoading(true);
    setError("");
    setSelectedNode(null);
    setQuizData(null);
    setExplainFeedback(null);
    setExplainText("");
    setCheckMode("select");
    
    try {
      const data = await api.getGraph(workspaceId);
      if (data && data.nodes && data.nodes.length > 0) {
        setGraphData(data);
      } else {
        setGraphData(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateGraph = async () => {
    setLoading(true);
    setError("");
    try {
      await api.generateGraph(workspaceId);
      await loadGraph();
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const handleSelectNode = (node) => {
    setSelectedNode(node);
    setQuizData(null);
    setQuizScore(null);
    setQuizFinished(false);
    setExplainText("");
    setExplainFeedback(null);
    setCheckMode("select");
    setUserAnswers({});
    
    // Wire context to Copilot chat
    if (setActiveNodeContext) {
      setActiveNodeContext({
        title: node.title,
        summary: node.summary
      });
    }
  };

  // Close node inspector
  const handleCloseInspector = () => {
    setSelectedNode(null);
    if (setActiveNodeContext) {
      setActiveNodeContext(null);
    }
  };

  // Start Node mini-quiz
  const handleStartQuiz = async () => {
    setLoading(true);
    setError("");
    try {
      const quiz = await api.getNodeQuiz(workspaceId, selectedNode.id);
      setQuizData(quiz);
      setQuizScore(null);
      setQuizFinished(false);
      setUserAnswers({});
      setCheckMode("quiz");
    } catch (err) {
      setError("Failed to generate quiz: " + err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectOption = (qIdx, optionKey) => {
    if (quizFinished) return;
    setUserAnswers(prev => ({ ...prev, [qIdx]: optionKey }));
  };

  const handleSubmitQuiz = async () => {
    if (!quizData) return;
    let score = 0;
    quizData.forEach((q, idx) => {
      if (userAnswers[idx] === q.answer) score++;
    });
    
    setQuizScore(score);
    setQuizFinished(true);

    try {
      // Submit result to backend
      const res = await api.attemptNode(workspaceId, selectedNode.id, {
        explain_mode: false,
        score: score
      });
      // Reload graph to update lock states
      const updatedGraph = await api.getGraph(workspaceId);
      setGraphData(updatedGraph);
    } catch (err) {
      console.error(err);
    }
  };

  // Explain-Back Mastery Submission
  const handleSubmitExplanation = async () => {
    if (!explainText || explainText.trim().length < 10) {
      setError("Please write a conceptual explanation containing at least 10 characters.");
      return;
    }
    setGrading(true);
    setError("");
    setExplainFeedback(null);
    try {
      const res = await api.attemptNode(workspaceId, selectedNode.id, {
        explain_mode: true,
        explanation: explainText
      });
      setExplainFeedback(res);
      // Reload graph to update locked/unlocked nodes
      const updatedGraph = await api.getGraph(workspaceId);
      setGraphData(updatedGraph);
    } catch (err) {
      setError("Grading failed: " + err.message);
    } finally {
      setGrading(false);
    }
  };

  // Topological rank layout calculations
  const calculateNodePositions = () => {
    if (!graphData || !graphData.nodes) return { positions: {}, colWidth: 260, rowHeight: 120 };

    const nodes = graphData.nodes;
    const edges = graphData.edges || [];
    
    // Create prereq and dependent dictionaries
    const prereqs = {};
    nodes.forEach(n => prereqs[n.id] = []);
    edges.forEach(e => {
      if (prereqs[e.to_node_id]) {
        prereqs[e.to_node_id].push(e.from_node_id);
      }
    });

    const ranks = {};
    let remaining = [...nodes];
    let changed = true;
    let iterations = 0;
    
    while (remaining.length > 0 && changed && iterations < 100) {
      changed = false;
      iterations++;
      const nextRemaining = [];
      
      for (const node of remaining) {
        const nodePrereqs = prereqs[node.id];
        if (nodePrereqs.length === 0) {
          ranks[node.id] = 0;
          changed = true;
        } else {
          const allRanked = nodePrereqs.every(pid => ranks[pid] !== undefined);
          if (allRanked) {
            const maxPrereqRank = Math.max(...nodePrereqs.map(pid => ranks[pid]));
            ranks[node.id] = maxPrereqRank + 1;
            changed = true;
          } else {
            nextRemaining.push(node);
          }
        }
      }
      remaining = nextRemaining;
    }

    // Fallback for circular dependencies or isolated nodes
    remaining.forEach(node => {
      ranks[node.id] = 0;
    });

    // Group node ids by columns
    const columns = {};
    nodes.forEach(node => {
      const col = ranks[node.id] || 0;
      if (!columns[col]) columns[col] = [];
      columns[col].push(node.id);
    });

    // Compute coordinates
    const positions = {};
    const COL_WIDTH = 260;
    const ROW_HEIGHT = 120;
    const NODE_WIDTH = 200;
    const NODE_HEIGHT = 70;

    Object.keys(columns).forEach(colStr => {
      const col = parseInt(colStr);
      const nodeIds = columns[col];
      nodeIds.forEach((nid, rowIdx) => {
        positions[nid] = {
          x: col * COL_WIDTH + 50,
          y: rowIdx * ROW_HEIGHT + 50,
          w: NODE_WIDTH,
          h: NODE_HEIGHT
        };
      });
    });

    return { positions, colWidth: COL_WIDTH, rowHeight: ROW_HEIGHT };
  };

  const { positions } = calculateNodePositions();

  // Find prerequisite titles for selected node
  const getPrerequisiteTitles = (node) => {
    if (!graphData || !node) return [];
    const prereqIds = graphData.edges
      .filter(e => e.to_node_id === node.id)
      .map(e => e.from_node_id);
    return graphData.nodes
      .filter(n => prereqIds.includes(n.id))
      .map(n => n.title);
  };

  return (
    <div className="concept-graph-panel-wrapper">
      {error && <div className="error-banner">{error}</div>}

      {!graphData ? (
        <section className="card center-setup">
          <span className="flow-welcome-icon">⛓️</span>
          <h3>Concept Map Gated Learning</h3>
          <p>
            Gemini will extract topics and build prerequisite pathways. Unlock topics one by one by passing mastery checks.
          </p>
          {documents.length === 0 ? (
            <div className="warning-box">
              ⚠️ Please upload your syllabus or study materials in the <strong>Materials</strong> tab first to start generating your Concept Map.
            </div>
          ) : (
            <button className="primary-btn" onClick={handleGenerateGraph} disabled={loading}>
              {loading ? "Analyzing syllabus & building DAG..." : "Generate Concept Map"}
            </button>
          )}
        </section>
      ) : (
        <div className="concept-graph-workspace">
          {/* Left Canvas Panel */}
          <div className="graph-canvas-container card">
            <div className="graph-canvas-header">
              <h4>Concept Mastery Pathways</h4>
              <div className="graph-legend">
                <span className="legend-item"><span className="legend-dot locked" /> Locked</span>
                <span className="legend-item"><span className="legend-dot unlocked" /> Unlocked</span>
                <span className="legend-item"><span className="legend-dot mastered" /> Mastered</span>
                <button className="reset-btn" onClick={handleGenerateGraph}>Rebuild Graph</button>
              </div>
            </div>
            
            <div className="graph-scroll-box" ref={graphContainerRef}>
              <div className="graph-viewport-area">
                {/* SVG Connections Overlay (Placed behind nodes) */}
                <svg className="graph-edges-svg">
                  <defs>
                    <marker id="arrow" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#3b4256" />
                    </marker>
                    <marker id="arrow-active" viewBox="0 0 10 10" refX="18" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                      <path d="M 0 1 L 10 5 L 0 9 z" fill="#6366f1" />
                    </marker>
                  </defs>
                  {graphData.edges?.map(edge => {
                    const fromPos = positions[edge.from_node_id];
                    const toPos = positions[edge.to_node_id];
                    if (!fromPos || !toPos) return null;

                    const fromMastery = graphData.masteries[edge.from_node_id];
                    const isEdgeActive = fromMastery?.status === "mastered";

                    // Draw curves from right edge of fromNode to left edge of toNode
                    const x1 = fromPos.x + fromPos.w;
                    const y1 = fromPos.y + fromPos.h / 2;
                    const x2 = toPos.x;
                    const y2 = toPos.y + toPos.h / 2;
                    const cx = (x1 + x2) / 2;

                    return (
                      <path
                        key={edge.id}
                        d={`M ${x1} ${y1} C ${cx} ${y1}, ${cx} ${y2}, ${x2} ${y2}`}
                        className={`graph-edge-path ${isEdgeActive ? "active" : ""}`}
                        markerEnd={`url(#${isEdgeActive ? "arrow-active" : "arrow"})`}
                      />
                    );
                  })}
                </svg>

                {/* Concept Node Cards */}
                {graphData.nodes?.map(node => {
                  const pos = positions[node.id];
                  if (!pos) return null;
                  
                  const mastery = graphData.masteries[node.id] || { status: "locked" };
                  const isSelected = selectedNode && selectedNode.id === node.id;
                  
                  return (
                    <div
                      key={node.id}
                      className={`concept-graph-node-card ${mastery.status} ${isSelected ? "selected" : ""}`}
                      style={{
                        left: `${pos.x}px`,
                        top: `${pos.y}px`,
                        width: `${pos.w}px`,
                        height: `${pos.h}px`,
                      }}
                      onClick={() => handleSelectNode(node)}
                    >
                      <div className="node-status-badge">
                        {mastery.status === "mastered" ? "✓" : mastery.status === "unlocked" ? "●" : "🔒"}
                      </div>
                      <div className="node-body">
                        <h6>{node.title}</h6>
                        <div style={{ display: "flex", gap: 4, alignItems: "center", marginTop: 2 }}>
                          {node.unit_ref && <span className="node-difficulty" style={{ background: "rgba(99,102,241,0.15)", color: "var(--accent)" }}>{node.unit_ref}</span>}
                          {node.difficulty && !["laq", "saq"].includes(node.difficulty.toLowerCase()) && (
                            <span className="node-difficulty">{node.difficulty}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Right Detail Inspector Slide-over */}
          {selectedNode && (
            <div className="concept-inspector-pane card animate-slide-left">
              <div className="inspector-top-bar">
                <h5>Concept Inspector</h5>
                <button className="close-btn" onClick={handleCloseInspector}>✕ Close</button>
              </div>

              <div className="inspector-scroll-body">
                <h3>{selectedNode.title}</h3>
                {selectedNode.unit_ref && (
                  <span className="prereq-tag" style={{ background: "rgba(99,102,241,0.15)", color: "var(--accent)", marginBottom: 8, display: "inline-block" }}>
                    📁 {selectedNode.unit_ref}
                  </span>
                )}
                
                {/* Prerequisites list */}
                <div className="inspector-prereqs-box">
                  <strong>Prerequisites:</strong>{" "}
                  {getPrerequisiteTitles(selectedNode).length === 0 ? (
                    <span className="no-prereqs">None (Starter Concept)</span>
                  ) : (
                    getPrerequisiteTitles(selectedNode).map((t, idx) => (
                      <span key={idx} className="prereq-tag">{t}</span>
                    ))
                  )}
                </div>

                <div className="concept-summary-card">
                  <h5>Concept Summary</h5>
                  <p>{selectedNode.summary}</p>
                </div>

                <hr className="divider" />

                {/* Gated Mastery Action */}
                <div className="concept-mastery-action">
                  {graphData.masteries[selectedNode.id]?.status === "locked" ? (
                    <div className="locked-challenge-box">
                      <span className="lock-icon">🔒</span>
                      <h5>Concept Locked</h5>
                      <p>This concept requires you to master its prerequisites before you can attempt it.</p>
                    </div>
                  ) : (
                    <div className="unlocked-challenge-box">
                      {checkMode === "select" && (
                        <>
                          <h5>Mastery Gated Check</h5>
                          <p>Unlock dependent pathways by proving your understanding of this topic:</p>
                          
                          {graphData.masteries[selectedNode.id]?.status === "mastered" && (
                            <div className="success-banner">
                              🎉 Concept Mastered! You can retry or move to other unlocked nodes.
                            </div>
                          )}

                          <div className="check-selection-grid">
                            <button className="selection-card" onClick={handleStartQuiz}>
                              <span className="icon">📊</span>
                              <strong>Practice MCQ Quiz</strong>
                              <span>3 direct questions</span>
                            </button>

                            <button className="selection-card" onClick={() => setCheckMode("explain")}>
                              <span className="icon">✍️</span>
                              <strong>Active Recall Explain-Back</strong>
                              <span>Gemini AI grading & feedback</span>
                            </button>
                          </div>
                        </>
                      )}

                      {checkMode === "quiz" && quizData && (
                        <div className="node-quiz-pane">
                          <h5>Mini-Quiz</h5>
                          {quizData.map((q, qIdx) => (
                            <div key={qIdx} className="quiz-q-item">
                              <p className="q-text"><strong>Q{qIdx + 1}:</strong> {q.question}</p>
                              <div className="options-grid">
                                {Object.entries(q.options).map(([key, val]) => {
                                  const isSelected = userAnswers[qIdx] === key;
                                  let optionClass = "";
                                  
                                  if (quizFinished) {
                                    if (key === q.answer) {
                                      optionClass = "correct-option";
                                    } else if (isSelected) {
                                      optionClass = "wrong-option";
                                    }
                                  } else if (isSelected) {
                                    optionClass = "selected-option";
                                  }

                                  return (
                                    <button
                                      key={key}
                                      className={`option-btn ${optionClass}`}
                                      onClick={() => handleSelectOption(qIdx, key)}
                                      disabled={quizFinished}
                                    >
                                      <strong>{key}.</strong> {val}
                                    </button>
                                  );
                                })}
                              </div>
                            </div>
                          ))}

                          {!quizFinished ? (
                            <button
                              className="primary-btn submit-quiz-btn"
                              onClick={handleSubmitQuiz}
                              disabled={Object.keys(userAnswers).length < quizData.length}
                            >
                              Submit Quiz Answers
                            </button>
                          ) : (
                            <div className="quiz-results-banner">
                              <h5>
                                Score: {quizScore} / {quizData.length}
                              </h5>
                              {quizScore >= 2 ? (
                                <p className="success-msg">🎉 Mastery Cleared! Dependent nodes are now unlocked.</p>
                              ) : (
                                <p className="fail-msg">❌ Did not pass (Requires 2/3). Re-read summary and retry.</p>
                              )}
                              <button className="retry-btn" onClick={() => setCheckMode("select")}>
                                Back to Selection
                              </button>
                            </div>
                          )}
                        </div>
                      )}

                      {checkMode === "explain" && (
                        <div className="explain-back-pane">
                          <h5>Explain-Back Active Recall</h5>
                          <p className="subtitle">Type a detailed explanation of this concept. Gemini will grade it against the core summary.</p>
                          
                          <textarea
                            rows={6}
                            placeholder="Write your explanation here (e.g. process context switching involves saving the CPU registers of the active thread, switching control to the kernel scheduler, loading state...)"
                            value={explainText}
                            onChange={(e) => setExplainText(e.target.value)}
                            disabled={grading}
                          />

                          <div className="actions-row">
                            <button 
                              className="secondary-btn" 
                              onClick={() => setCheckMode("select")}
                              disabled={grading}
                            >
                              Cancel
                            </button>
                            <button 
                              className="primary-btn submit-explanation-btn" 
                              onClick={handleSubmitExplanation}
                              disabled={grading || explainText.trim().length < 10}
                            >
                              {grading ? "🤖 Grading Answer..." : "Submit Explanation"}
                            </button>
                          </div>

                          {explainFeedback && (
                            <div className={`explanation-feedback-box ${explainFeedback.passed ? "passed" : "failed"}`}>
                              <h6>Grade Score: {explainFeedback.score}/100</h6>
                              {explainFeedback.passed ? (
                                <p className="status-msg green">🎉 Passed! Prerequisite pathway unlocked.</p>
                              ) : (
                                <p className="status-msg red">❌ Did not pass yet. Read the advice below and try explaining it again.</p>
                              )}
                              <hr className="inner-divider" />
                              <p className="feedback-text">{explainFeedback.feedback}</p>
                              <button className="retry-btn" onClick={() => setExplainFeedback(null)}>
                                Try Explaining Again
                              </button>
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
