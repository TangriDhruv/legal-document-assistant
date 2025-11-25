import React, { useEffect, useRef } from "react";

interface ChatInterfaceProps {
  conversation: Array<{ role: string; content: string }>;
  onSendMessage: (message: string) => Promise<void>;
  loading: boolean;
}

export function ChatInterface({
  conversation,
  onSendMessage,
  loading,
}: ChatInterfaceProps) {
  const [input, setInput] = React.useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [conversation]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    await onSendMessage(input);
    setInput("");
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {conversation.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            {msg.role === "assistant" && <span className="role-icon">🤖 </span>}
            {msg.role === "user" && <span className="role-icon">👤 </span>}
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="message assistant">
            <span className="role-icon">🤖 </span>
            <div className="message-content typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Tell me about the placeholders..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading} className="send-btn">
          {loading ? "..." : "Send"}
        </button>
      </form>
    </div>
  );
}