import MarkdownRenderer from "./MarkdownRenderer";

export default function ChatPanel({
  chatHistory,
  chatInput,
  setChatInput,
  handleSendChat,
}) {
  return (
    <section className="chat-panel-container">
      <h4>AI Copilot Chat</h4>

      <div className="chat-box">
        {chatHistory.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message-bubble ${msg.role}`}
          >
            <div className="chat-avatar">
              {msg.role === "user" ? "👤" : "🤖"}
            </div>
            <div className="chat-bubble-content">
              <MarkdownRenderer content={msg.message} />
            </div>
          </div>
        ))}
      </div>

      <form onSubmit={handleSendChat}>
        <input
          type="text"
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          placeholder="Ask about your study material"
        />
        <button type="submit">Send</button>
      </form>
    </section>
  );
}