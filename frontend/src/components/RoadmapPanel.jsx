import { useEffect, useState } from "react";
import { api } from "../api";

export default function RoadmapPanel({ workspaceId, documents }) {
  const [roadmap, setRoadmap] = useState(null);
  const [activeUnit, setActiveUnit] = useState(null);
  const [unitData, setUnitData] = useState(null);
  const [userAnswers, setUserAnswers] = useState({});
  const [quizScore, setQuizScore] = useState(null);
  const [showReview, setShowReview] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    loadRoadmap();
  }, [workspaceId]);

  async function loadRoadmap() {
    setLoading(true);
    setError("");
    try {
      const data = await api.getRoadmap(workspaceId);
      if (data && data.units && data.units.length > 0) {
        setRoadmap(data);
      } else {
        setRoadmap(null);
      }
      setActiveUnit(null);
      setUnitData(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleGenerateRoadmap() {
    setLoading(true);
    setError("");
    try {
      const data = await api.generateRoadmap(workspaceId);
      setRoadmap(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleSelectUnit(unit) {
    if (!unit.unlocked) return;
    setLoading(true);
    setError("");
    setActiveUnit(unit);
    setUnitData(null);
    setUserAnswers({});
    setQuizScore(null);
    setShowReview(false);

    try {
      const data = await api.learnRoadmapStep(workspaceId, unit.id);
      setUnitData(data);
    } catch (err) {
      setError(err.message);
      setActiveUnit(null);
    } finally {
      setLoading(false);
    }
  }

  async function handleAnswerOption(qIdx, optionKey) {
    if (showReview) return;
    setUserAnswers((prev) => ({
      ...prev,
      [qIdx]: optionKey,
    }));
  }

  async function handleSubmitQuiz() {
    if (!unitData || !unitData.quiz) return;

    let score = 0;
    const total = unitData.quiz.length;

    unitData.quiz.forEach((q, idx) => {
      if (userAnswers[idx] === q.answer) {
        score++;
      }
    });

    setQuizScore(score);
    setShowReview(true);

    // If student gets at least 2/3 (or passed), unlock next step on backend
    const passed = score >= 2;
    if (passed && activeUnit) {
      try {
        const updatedRoadmap = await api.completeRoadmapStep(workspaceId, activeUnit.id);
        setRoadmap(updatedRoadmap);
      } catch (err) {
        console.error("Failed to update step progress:", err);
      }
    }
  }

  async function handleResetRoadmap() {
    if (!window.confirm("Are you sure you want to delete this roadmap and start over?")) return;
    setLoading(true);
    try {
      await api.resetRoadmap(workspaceId);
      setRoadmap(null);
      setActiveUnit(null);
      setUnitData(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  function formatMarkdown(text) {
    if (!text) return "";
    let html = text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");

    // Bold formatting
    html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    
    // Header formatting
    html = html.replace(/^### (.*?)$/gm, "<h3>$1</h3>");
    html = html.replace(/^## (.*?)$/gm, "<h2>$1</h2>");
    html = html.replace(/^# (.*?)$/gm, "<h1>$1</h1>");
    
    // Lists formatting
    html = html.replace(/^\* (.*?)$/gm, "<li>$1</li>");
    html = html.replace(/^- (.*?)$/gm, "<li>$1</li>");
    
    // Code blocks
    html = html.replace(/```(.*?)```/gs, "<pre><code>$1</code></pre>");
    
    // Convert double newlines to paragraph blocks
    html = html.split("\n\n").map(p => {
      if (p.trim().startsWith("<h") || p.trim().startsWith("<li") || p.trim().startsWith("<pre")) {
        return p;
      }
      return `<p>${p.replace(/\n/g, "<br/>")}</p>`;
    }).join("");

    return html;
  }

  if (loading && !unitData && !roadmap) {
    return <div className="card loading-placeholder">⏳ Generating roadmap units... Please wait</div>;
  }

  return (
    <div className="roadmap-panel">
      {error && <div className="error-banner">{error}</div>}

      {!roadmap ? (
        <section className="card center-setup">
          <h3>Guided Study Roadmap</h3>
          <p>
            Build a step-by-step preparation plan customized to your course materials.
          </p>
          {documents.length === 0 ? (
            <div className="warning-box">
              ⚠️ Please upload your syllabus or study materials in the <strong>Materials</strong> tab first to start generating your learning path.
            </div>
          ) : (
            <button className="primary-btn" onClick={handleGenerateRoadmap} disabled={loading}>
              {loading ? "Analyzing Syllabus..." : "Generate Preparation Roadmap"}
            </button>
          )}
        </section>
      ) : (
        <div className="roadmap-workspace">
          {/* Left timeline side */}
          <div className="roadmap-sidebar card">
            <div className="roadmap-header">
              <h4>Preparation Roadmap</h4>
              <button className="reset-btn" onClick={handleResetRoadmap}>Reset Roadmap</button>
            </div>
            
            <div className="roadmap-timeline">
              {roadmap.units.map((unit) => {
                const isActive = activeUnit && activeUnit.id === unit.id;
                let statusClass = "locked";
                if (unit.completed) statusClass = "completed";
                else if (unit.unlocked) statusClass = "unlocked";

                return (
                  <div
                    key={unit.id}
                    className={`timeline-step ${statusClass} ${isActive ? "active" : ""}`}
                    onClick={() => unit.unlocked && handleSelectUnit(unit)}
                  >
                    <div className="status-indicator">
                      {unit.completed ? "✓" : unit.unlocked ? unit.id : "🔒"}
                    </div>
                    <div className="step-info">
                      <h5>{unit.title}</h5>
                      <span className="topic-tags">
                        {unit.topics.slice(0, 3).join(" • ")}
                        {unit.topics.length > 3 && "..."}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Right reading and practice side */}
          <div className="roadmap-content card">
            {activeUnit ? (
              <div className="unit-learn-view">
                <h3>{activeUnit.title}</h3>
                
                {loading && !unitData ? (
                  <div className="loading-placeholder">
                    ⏳ Generating customized study notes and quiz questions for this unit...
                  </div>
                ) : unitData ? (
                  <div className="unit-container">
                    {/* Material reading */}
                    <div className="material-reader">
                      <h4>Study Material</h4>
                      <div 
                        className="markdown-body" 
                        dangerouslySetInnerHTML={{ __html: formatMarkdown(unitData.material) }} 
                      />
                    </div>

                    {/* Mini Quiz */}
                    <div className="material-quiz">
                      <hr />
                      <h4>Verify Understanding (Quiz)</h4>
                      <p className="quiz-subtitle">Answer at least 2 questions correctly to unlock the next unit.</p>
                      
                      {unitData.quiz.map((q, qIdx) => (
                        <div key={qIdx} className="mini-quiz-question">
                          <p className="q-text"><strong>Q{qIdx + 1}:</strong> {q.question}</p>
                          <div className="options-grid">
                            {Object.entries(q.options).map(([key, val]) => {
                              const isSelected = userAnswers[qIdx] === key;
                              let optionClass = "";
                              
                              if (showReview) {
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
                                  onClick={() => handleAnswerOption(qIdx, key)}
                                  disabled={showReview}
                                >
                                  <strong>{key}.</strong> {val}
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))}

                      {!showReview ? (
                        <button
                          className="primary-btn submit-quiz-btn"
                          onClick={handleSubmitQuiz}
                          disabled={Object.keys(userAnswers).length < unitData.quiz.length}
                        >
                          Submit Practice Answers
                        </button>
                      ) : (
                        <div className="quiz-results-banner">
                          <h5>
                            Score: {quizScore} / {unitData.quiz.length}
                          </h5>
                          {quizScore >= 2 ? (
                            <p className="success-msg">🎉 Passed! Next unit is unlocked. You can select it in the sidebar.</p>
                          ) : (
                            <p className="fail-msg">❌ Did not pass. Try re-reading the study content and take the quiz again.</p>
                          )}
                          <button className="retry-btn" onClick={() => handleSelectUnit(activeUnit)}>
                            Retry Unit
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                ) : null}
              </div>
            ) : (
              <div className="empty-content-state">
                <h4>Welcome to Guided Preparation Mode</h4>
                <p>Select an unlocked unit from the timeline to start studying and verify your knowledge.</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
