export default function ChatPanel({
  chatHistory,
  chatInput,
  setChatInput,
  handleSendChat,
}) {
  return (
    <section className="card">
      <h4>Workspace Chat</h4>

      <div className="chat-box">
         {chatHistory.map((msg) => (
        <div
          key={msg.id}
          className={`chat-message ${msg.role}`}
        >
        <p>{msg.message}</p>
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