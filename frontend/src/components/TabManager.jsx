import React, { useEffect, useRef } from "react";
import MarkdownRenderer from "./MarkdownRenderer";
import { X, Send, Loader2, MessageSquare, FileText, BookOpen, Check, MapPin } from "lucide-react";

/**
 * TabManager — center panel with browser-style tabs.
 *
 * Each tab: { id, type: 'chat'|'document'|'node_answer', label, icon, data }
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

  return (
    <div className="doc-viewer-panel">
      <div className="doc-viewer-header">
        <FileText size={18} style={{ color: "var(--accent)" }} />
        <h3>{doc?.filename || "Document"}</h3>
      </div>
      {loading ? (
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
  );
}

/* ---- Node Answer Tab ---- */
function NodeAnswerTabContent({ tab, onMarkMastered, onOpenChat, mastery }) {
  const { data } = tab;
  const isMastered = mastery?.status === "mastered";

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

      <div className="node-answer-content">
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
