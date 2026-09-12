import React, { useState, useEffect, useRef } from "react";
import { api } from "../api";

export default function LogicFlowPanel({ workspaceId, documents, contentHistory, loadContentHistory }) {
  const [topic, setTopic] = useState("");
  const [selectedDocumentId, setSelectedDocumentId] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  // Logic Flow State
  const [selectedFlow, setSelectedFlow] = useState(null);
  const [flowData, setFlowData] = useState(null);
  
  // Simulator State
  const [activeStepId, setActiveStepId] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playSpeed, setPlaySpeed] = useState(3000); // 3 seconds
  
  const timerRef = useRef(null);
  const timelineRef = useRef(null);

  // Filter history to only get logic flows
  const logicFlowHistory = contentHistory.filter(item => item.content_type === "logic_flow");

  // Load history when workspace changes
  useEffect(() => {
    setSelectedFlow(null);
    setFlowData(null);
    setActiveStepId(null);
    setIsPlaying(false);
    stopSimulation();
  }, [workspaceId]);

  // Clean up timer on unmount
  useEffect(() => {
    return () => stopSimulation();
  }, []);

  // Simulator Player Logic
  useEffect(() => {
    if (isPlaying && flowData && flowData.steps && flowData.steps.length > 0) {
      timerRef.current = setTimeout(() => {
        progressSimulation();
      }, playSpeed);
    }
    return () => clearTimeout(timerRef.current);
  }, [isPlaying, activeStepId, flowData, playSpeed]);

  const stopSimulation = () => {
    setIsPlaying(false);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }
  };

  const startSimulation = () => {
    if (!flowData || !flowData.steps || flowData.steps.length === 0) return;
    setIsPlaying(true);
    if (activeStepId === null) {
      setActiveStepId(flowData.steps[0].id);
    }
  };

  const handleResetSimulation = () => {
    stopSimulation();
    if (flowData && flowData.steps && flowData.steps.length > 0) {
      setActiveStepId(flowData.steps[0].id);
    } else {
      setActiveStepId(null);
    }
  };

  const handleStepForward = () => {
    stopSimulation();
    progressSimulation();
  };

  const handleStepBackward = () => {
    stopSimulation();
    if (!flowData || !flowData.steps || activeStepId === null) return;
    
    const currentIndex = flowData.steps.findIndex(s => s.id === activeStepId);
    if (currentIndex > 0) {
      setActiveStepId(flowData.steps[currentIndex - 1].id);
      scrollToActiveStep(flowData.steps[currentIndex - 1].id);
    }
  };

  const progressSimulation = () => {
    if (!flowData || !flowData.steps || activeStepId === null) return;

    const currentStep = flowData.steps.find(s => s.id === activeStepId);
    if (!currentStep) return;

    // Handle condition branches
    if (currentStep.type === "condition") {
      // For simulator, default to Yes branch or just next sequential step
      const targetId = currentStep.yes_step_id || currentStep.next_step_id;
      if (targetId && flowData.steps.some(s => s.id === targetId)) {
        setActiveStepId(targetId);
        scrollToActiveStep(targetId);
        return;
      }
    }

    // Default sequential progression
    const currentIndex = flowData.steps.findIndex(s => s.id === activeStepId);
    if (currentIndex !== -1 && currentIndex + 1 < flowData.steps.length) {
      const nextStep = flowData.steps[currentIndex + 1];
      setActiveStepId(nextStep.id);
      scrollToActiveStep(nextStep.id);
    } else {
      // Loop back or finish
      stopSimulation();
    }
  };

  const scrollToActiveStep = (stepId) => {
    setTimeout(() => {
      const element = document.getElementById(`step-node-${stepId}`);
      if (element) {
        element.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
    }, 100);
  };

  const handleSelectFlowFromHistory = (item) => {
    stopSimulation();
    setError("");
    setSelectedFlow(item);
    try {
      let cleaned = item.content.replace(/```json/gi, "").replace(/```/g, "").trim();
      let parsed;
      try {
        parsed = JSON.parse(cleaned);
      } catch (_) {
        // Repair unterminated strings or unclosed brackets
        let repaired = cleaned;
        const quoteMatches = repaired.match(/(?<!\\)"/g) || [];
        if (quoteMatches.length % 2 !== 0) repaired += '"';

        const openBraces = (repaired.match(/\{/g) || []).length;
        const closeBraces = (repaired.match(/\}/g) || []).length;
        const openBrackets = (repaired.match(/\[/g) || []).length;
        const closeBrackets = (repaired.match(/\]/g) || []).length;

        for (let i = 0; i < openBrackets - closeBrackets; i++) repaired += "]";
        for (let i = 0; i < openBraces - closeBraces; i++) repaired += "}";

        parsed = JSON.parse(repaired);
      }
      setFlowData(parsed);
      if (parsed.steps && parsed.steps.length > 0) {
        setActiveStepId(parsed.steps[0].id);
      }
    } catch (err) {
      setError("Failed to parse logic flow JSON: " + err.message);
      setFlowData(null);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError("");
    setSelectedFlow(null);
    setFlowData(null);
    setActiveStepId(null);
    stopSimulation();

    try {
      const res = await api.generateLogicFlow(workspaceId, {
        topic: topic || null,
        document_id: selectedDocumentId || null,
      });
      await loadContentHistory(workspaceId);
      handleSelectFlowFromHistory(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteFlow = async (itemId, e) => {
    e.stopPropagation();
    if (!window.confirm("Delete this Logic Flow?")) return;
    try {
      await api.deleteContent(workspaceId, itemId);
      await loadContentHistory(workspaceId);
      if (selectedFlow && selectedFlow.id === itemId) {
        setSelectedFlow(null);
        setFlowData(null);
        setActiveStepId(null);
        stopSimulation();
      }
    } catch (err) {
      setError("Failed to delete: " + err.message);
    }
  };

  const activeStepDetail = flowData?.steps?.find(s => s.id === activeStepId);

  return (
    <div className="logic-flow-workspace">
      {error && <div className="error-banner">{error}</div>}

      <div className="logic-flow-grid">
        {/* Left Side: Creation Form & History list */}
        <div className="flow-control-panel card">
          <h4>Study Logic Flow</h4>
          <p className="subtitle">Visualize complex processes, loops, and conditional algorithms step-by-step.</p>
          
          <div className="generation-form">
            <input
              type="text"
              placeholder="Enter process name (e.g. process context switch)"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
            />
            
            <div className="form-row">
              <label>Source Document:</label>
              <select
                value={selectedDocumentId}
                onChange={(e) => setSelectedDocumentId(e.target.value)}
              >
                <option value="">All Documents</option>
                {documents.map((doc) => (
                  <option key={doc.id} value={doc.id}>
                    {doc.filename}
                  </option>
                ))}
              </select>
            </div>
            
            <button 
              className="primary-btn generate-flow-btn" 
              onClick={handleGenerate} 
              disabled={loading}
            >
              {loading ? "🤖 Generating Flow..." : "⚡ Generate Flowchart"}
            </button>
          </div>

          <div className="flow-history-section">
            <h5>Generated Flows</h5>
            {logicFlowHistory.length === 0 ? (
              <p className="no-history-text">No logic flows generated yet.</p>
            ) : (
              <ul className="flow-history-list">
                {logicFlowHistory.map((item) => (
                  <li 
                    key={item.id} 
                    className={`flow-history-item ${selectedFlow?.id === item.id ? "active" : ""}`}
                    onClick={() => handleSelectFlowFromHistory(item)}
                  >
                    <span className="flow-title-text">🔗 {item.title}</span>
                    <button 
                      className="delete-item-btn" 
                      onClick={(e) => handleDeleteFlow(item.id, e)}
                      title="Delete Flow"
                    >
                      ✕
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Right Side: Flowchart Viewer & Active step inspector */}
        <div className="flow-visual-panel">
          {loading ? (
            <div className="card empty-flow-state loading">
              <span className="spinner">⏳</span>
              <h4>Analyzing Study Material...</h4>
              <p>Gemini is tracing the process sequence and preparing an interactive logic map.</p>
            </div>
          ) : flowData ? (
            <div className="flow-viewer-inner">
              <div className="flow-header card">
                <div className="flow-header-info">
                  <h3>{flowData.title}</h3>
                  <p>{flowData.description}</p>
                </div>
                
                {/* Simulation Control Player */}
                <div className="simulation-player">
                  <button 
                    className="player-btn prev-btn" 
                    onClick={handleStepBackward}
                    disabled={!flowData.steps || activeStepId === flowData.steps[0]?.id}
                    title="Previous Step"
                  >
                    ⏮️
                  </button>
                  {isPlaying ? (
                    <button className="player-btn pause-btn" onClick={stopSimulation} title="Pause">
                      ⏸️ Pause
                    </button>
                  ) : (
                    <button className="player-btn play-btn" onClick={startSimulation} title="Play Simulation">
                      ▶️ Play
                    </button>
                  )}
                  <button 
                    className="player-btn next-btn" 
                    onClick={handleStepForward}
                    disabled={!flowData.steps || activeStepId === flowData.steps[flowData.steps.length - 1]?.id}
                    title="Next Step"
                  >
                    ⏭️
                  </button>
                  <button className="player-btn reset-btn" onClick={handleResetSimulation} title="Reset to Start">
                    🔄 Reset
                  </button>
                  
                  <select 
                    className="speed-selector" 
                    value={playSpeed}
                    onChange={(e) => setPlaySpeed(Number(e.target.value))}
                    title="Simulation Step Speed"
                  >
                    <option value={5000}>Slow (5s)</option>
                    <option value={3000}>Medium (3s)</option>
                    <option value={1500}>Fast (1.5s)</option>
                  </select>
                </div>
              </div>

              <div className="flow-body-split">
                {/* Interactive Flowchart Area */}
                <div className="flowchart-container card" ref={timelineRef}>
                  <div className="flow-timeline">
                    {flowData.steps?.map((step, index) => {
                      const isActive = activeStepId === step.id;
                      const isLast = index === flowData.steps.length - 1;
                      
                      return (
                        <div key={step.id} className="flow-step-wrapper">
                          <div 
                            id={`step-node-${step.id}`}
                            className={`flow-node-card ${step.type} ${isActive ? "active" : ""}`}
                            onClick={() => {
                              stopSimulation();
                              setActiveStepId(step.id);
                            }}
                          >
                            <div className="node-badge">{step.id}</div>
                            <div className="node-content">
                              <h6>{step.title}</h6>
                              <span className={`node-type-label ${step.type}`}>{step.type}</span>
                            </div>
                          </div>
                          
                          {!isLast && (
                            <div className={`flow-connector-line ${isActive && isPlaying ? "pulsing" : ""}`}>
                              <div className="connector-arrow">▼</div>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Detail Inspector Sidebar */}
                <div className="flow-inspector card">
                  {activeStepDetail ? (
                    <div className="inspector-content">
                      <div className="inspector-header">
                        <span className="step-num">Step {activeStepDetail.id}</span>
                        <span className={`badge-type ${activeStepDetail.type}`}>{activeStepDetail.type.toUpperCase()}</span>
                      </div>
                      <h4>{activeStepDetail.title}</h4>
                      
                      <div className="inspector-desc-box">
                        <p>{activeStepDetail.description}</p>
                      </div>

                      {activeStepDetail.type === "condition" && (
                        <div className="condition-branch-info">
                          <div className="branch yes">
                            <strong>Yes Path:</strong> Step {activeStepDetail.yes_step_id}
                          </div>
                          <div className="branch no">
                            <strong>No Path:</strong> Step {activeStepDetail.no_step_id}
                          </div>
                        </div>
                      )}
                      
                      {activeStepDetail.next_step_id && activeStepDetail.type !== "condition" && (
                        <div className="next-step-info">
                          <span>Next up: Step {activeStepDetail.next_step_id}</span>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="empty-inspector">
                      <p>Select any step in the flowchart to view details or click Play to run simulation.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="card empty-flow-state">
              <span className="flow-welcome-icon">⛓️</span>
              <h4>Interactive Logic Map Simulator</h4>
              <p>Type a technical topic or algorithm name on the left and select generate to see how it executes step-by-step.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
