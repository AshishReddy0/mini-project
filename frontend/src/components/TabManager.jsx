import React, { useEffect, useRef } from "react";
import MarkdownRenderer from "./MarkdownRenderer";
import VoiceInput from "./VoiceInput";
import { X, Send, Loader2, MessageSquare, FileText, BookOpen, Check, MapPin, User, Award, Clock, CheckCircle, AlertTriangle, LogOut } from "lucide-react";

/**
 * TabManager — center panel with browser-style tabs.
 *
 * Each tab: { id, type: 'chat'|'document'|'node_answer'|'profile', label, icon, data }
 * 'chat' tab is always pinned (no close button).
 */
export default function TabManager({
  tabs,
  activeTabId,
  onTabClick,
  onTabClose,
  chatHistory,
  chatInput,
  setChatInput,
  handleSendChat,
  chatLoading,
  activeNodeContext,
  onClearNodeContext,
  onOpenChatWithNode,
  // Node answer tab props
  onMarkMastered,
  masteries,
  workspaceId,
  // Profile props
  user,
  workspace,
  documentsCount = 0,
  graphNodes = [],
  focusSeconds = 0,
  onLogout,
}) {
  const activeTab = tabs.find((t) => t.id === activeTabId) || tabs[0];

  return (
    <div className="center-panel">
      {/* Tab Bar */}
      <div className="tab-bar">
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={`tab-item ${tab.id === activeTabId ? "active" : ""}`}
            onClick={() => onTabClick(tab.id)}
          >
            <span className="tab-icon" style={{ display: "flex", alignItems: "center" }}>
              {tab.icon}
            </span>
            <span className="tab-label">{tab.label}</span>
            {tab.type !== "chat" && (
              <button
                className="tab-close"
                style={{ display: "flex", alignItems: "center" }}
                onClick={(e) => { e.stopPropagation(); onTabClose(tab.id); }}
                title="Close tab"
              >
                <X size={10} />
              </button>
            )}
          </div>
        ))}
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab?.type === "chat" && (
          <ChatTabContent
            chatHistory={chatHistory}
            chatInput={chatInput}
            setChatInput={setChatInput}
            handleSendChat={handleSendChat}
            loading={chatLoading}
            activeNodeContext={activeNodeContext}
            onClearNodeContext={onClearNodeContext}
          />
        )}
        {activeTab?.type === "document" && (
          <DocumentTabContent doc={activeTab.data} />
        )}
        {activeTab?.type === "node_answer" && (
          <NodeAnswerTabContent
            tab={activeTab}
            onMarkMastered={onMarkMastered}
            onOpenChat={onOpenChatWithNode}
            mastery={masteries?.[activeTab.data?.nodeId]}
            workspaceId={workspaceId}
          />
        )}
      </div>
    </div>
  );
}

/* ---- Chat Tab ---- */
function ChatTabContent({ chatHistory, chatInput, setChatInput, handleSendChat, loading, activeNodeContext, onClearNodeContext }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatHistory]);

  return (
    <div className="chat-panel">
      {activeNodeContext && (
        <div className="chat-context-banner">
          <MapPin size={12} />
          <span>Context:</span>
          <span className="context-badge">{activeNodeContext.title}</span>
          <button className="context-clear-btn" style={{ display: "flex", alignItems: "center", gap: 3 }} onClick={onClearNodeContext}>
            <X size={10} /> Clear
          </button>
        </div>
      )}

      <div className="chat-messages-area">
        {chatHistory.length === 0 ? (
          <div className="chat-empty-state">
            <div className="chat-empty-icon" style={{ opacity: 0.8 }}>
              <MessageSquare size={36} />
            </div>
            <h4>AI Study Copilot</h4>
            <p>Ask anything about your study materials. Click a concept on the roadmap to focus the conversation.</p>
          </div>
        ) : (
          chatHistory.map((msg) => (
            <div key={msg.id} className={`chat-message ${msg.role}`}>
              <span className="message-role-label">{msg.role === "user" ? "You" : "Copilot"}</span>
              <div className="message-bubble">
                {msg.role === "assistant" ? (
                  <MarkdownRenderer content={msg.message} />
                ) : (
                  msg.message
                )}
              </div>
            </div>
          ))
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-area">
        <form className="chat-input-form" onSubmit={handleSendChat}>
          <textarea
            className="chat-input"
            rows={1}
            placeholder={activeNodeContext ? `Ask about "${activeNodeContext.title}"...` : "Ask anything about your materials..."}
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleSendChat(e);
              }
            }}
            disabled={loading}
          />
          <VoiceInput
            onTranscript={(spoken) =>
              setChatInput((prev) => (prev ? prev + " " + spoken : spoken))
            }
          />
          <button type="submit" className="chat-send-btn" disabled={loading || !chatInput.trim()}>
            {loading ? <Loader2 size={16} className="loading-spinner-animate" style={{ animation: "spin 1s linear infinite" }} /> : <Send size={14} />}
          </button>
        </form>
      </div>
    </div>
  );
}

/* ---- Document Tab ---- */
function DocumentTabContent({ doc }) {
  const [text, setText] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  const [viewMode, setViewMode] = React.useState("pdf"); // 'pdf' | 'text'

  useEffect(() => {
    if (!doc) return;
    if (doc.extractedText) {
      setText(doc.extractedText);
      setLoading(false);
    } else {
      setLoading(false);
      setText(null);
    }
  }, [doc]);

  const fileUrl = doc?.file_path
    ? `http://127.0.0.1:8000/${doc.file_path.replace(/\\/g, "/")}`
    : null;
  const isPdf = doc?.filename?.toLowerCase().endsWith(".pdf");

  return (
    <div className="doc-viewer-panel">
      <div className="doc-viewer-header">
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <FileText size={18} style={{ color: "var(--accent)" }} />
          <h3>{doc?.filename || "Document"}</h3>
        </div>

        <div className="doc-view-toggle">
          {isPdf && fileUrl && (
            <button
              className={`toggle-btn ${viewMode === "pdf" ? "active" : ""}`}
              onClick={() => setViewMode("pdf")}
            >
              📄 Visual PDF View
            </button>
          )}
          <button
            className={`toggle-btn ${viewMode === "text" || !isPdf ? "active" : ""}`}
            onClick={() => setViewMode("text")}
          >
            📝 Extracted Text
          </button>
        </div>
      </div>

      <div className="doc-viewer-container">
        {viewMode === "pdf" && isPdf && fileUrl ? (
          <iframe
            src={fileUrl}
            title={doc.filename}
            className="doc-pdf-iframe"
            width="100%"
            height="100%"
          />
        ) : loading ? (
          <div style={{ color: "var(--text-muted)", padding: "20px" }}>Loading...</div>
        ) : text ? (
          <div className="doc-viewer-body">{text}</div>
        ) : (
          <div style={{ color: "var(--text-muted)", padding: "20px", fontSize: "0.85rem" }}>
            No extracted text preview available for this file type.<br />
            The AI can still use it — just ask in chat!
          </div>
        )}
      </div>
    </div>
  );
}

/* ---- Node Answer Tab ---- */
function NodeAnswerTabContent({ tab, onMarkMastered, onOpenChat, mastery, workspaceId }) {
  const { data } = tab;
  const isMastered = mastery?.status === "mastered";

  // Active Recall Semantic Evaluator state
  const [explanationInput, setExplanationInput] = React.useState("");
  const [evaluating, setEvaluating] = React.useState(false);
  const [evalResult, setEvalResult] = React.useState(null);
  const [evalError, setEvalError] = React.useState("");

  async function handleEvaluateSemanticMeaning(e) {
    e.preventDefault();
    if (!explanationInput.trim() || explanationInput.trim().length < 10) {
      setEvalError("Please enter at least 10 characters explaining your understanding.");
      return;
    }
    setEvaluating(true);
    setEvalError("");
    try {
      const res = await api.attemptNode(workspaceId, data.nodeId, {
        explain_mode: true,
        explanation: explanationInput.trim(),
      });
      setEvalResult(res);
      if (res?.passed) {
        onMarkMastered(data.nodeId);
      }
    } catch (err) {
      setEvalError(err.message);
    } finally {
      setEvaluating(false);
    }
  }

  return (
    <div className="node-answer-panel">
      <div className="node-answer-header">
        <div className="node-answer-title-row">
          <h2 className="node-answer-title">{data?.title}</h2>
          {data?.difficulty && (
            <span className={`difficulty-badge ${data.difficulty}`}>{data.difficulty}</span>
          )}
        </div>

        {data?.summary && (
          <p className="node-answer-summary">{data.summary}</p>
        )}

        {data?.subPoints && data.subPoints.length > 0 && (
          <div className="sub-points-row">
            {data.subPoints.map((sp, i) => (
              <span key={i} className="sub-point-chip" title={sp.description}>
                {sp.title}
              </span>
            ))}
          </div>
        )}

        <div className="node-answer-actions">
          <button
            className="action-btn primary"
            style={{ display: "flex", alignItems: "center", gap: 6 }}
            onClick={() => onOpenChat({ title: data?.title, summary: data?.summary })}
          >
            <MessageSquare size={13} /> Ask Copilot about this
          </button>
          <button
            className={`action-btn success ${isMastered ? "mastered" : ""}`}
            style={{ display: "flex", alignItems: "center", gap: 6 }}
            onClick={() => !isMastered && onMarkMastered(data?.nodeId)}
            disabled={isMastered}
          >
            <Check size={13} /> {isMastered ? "Mastered" : "Mark as Mastered"}
          </button>
        </div>
      </div>

      {/* Semantic Answer Evaluator Card */}
      <div className="semantic-evaluator-card">
        <div className="evaluator-header">
          <h4>🧠 Test Your Semantic Understanding (Active Recall)</h4>
          <span className="evaluator-sub">Explain this concept in your own words. The AI checks meaning &amp; concepts — not exact sentences!</span>
        </div>

        <form onSubmit={handleEvaluateSemanticMeaning} className="evaluator-form">
          <div className="eval-input-wrapper">
            <textarea
              className="eval-textarea"
              rows={3}
              placeholder={`Explain what "${data?.title}" means in your own words...`}
              value={explanationInput}
              onChange={(e) => setExplanationInput(e.target.value)}
              disabled={evaluating}
            />
            <div className="eval-input-actions">
              <VoiceInput
                onTranscript={(spoken) =>
                  setExplanationInput((prev) => (prev ? prev + " " + spoken : spoken))
                }
              />
            </div>
          </div>

          <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 8 }}>
            <button
              type="submit"
              className="action-btn primary"
              disabled={evaluating || !explanationInput.trim()}
            >
              {evaluating ? "AI Evaluating Meaning…" : "Evaluate Semantic Meaning"}
            </button>
          </div>
        </form>

        {evalError && <div className="eval-error-msg">{evalError}</div>}

        {evalResult && (
          <div className={`eval-result-box ${evalResult.passed ? "passed" : "needs-work"}`}>
            <div className="eval-score-badge">
              <span className="score-num">{evalResult.score}%</span>
              <span className="score-label">{evalResult.passed ? "✅ Understood & Mastered!" : "💡 Conceptual Review Recommended"}</span>
            </div>

            <div className="eval-feedback-body">
              <MarkdownRenderer content={evalResult.feedback} />
            </div>
          </div>
        )}
      </div>

      <div className="node-answer-content">
        <h4 style={{ marginBottom: 12, color: "var(--text-main)" }}>📖 Complete Reference Study Answer</h4>
        {data?.loadingAnswer ? (
          <div className="node-answer-loading">
            <div className="loading-spinner" />
            <p>Generating reference answer from your materials...</p>
          </div>
        ) : data?.answer ? (
          <MarkdownRenderer content={data.answer} />
        ) : (
          <div className="node-answer-loading">
            <div className="loading-spinner" />
            <p>Loading...</p>
          </div>
        )}
      </div>
    </div>
  );
}
