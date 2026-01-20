import { useEffect, useRef, useState } from "react";
import type { Placeholder } from "../types";

interface ChatInterfaceProps {
  conversation: Array<{ role: string; content: string }>;
  onSendMessage: (message: string) => Promise<void>;
  loading: boolean;
  placeholders?: Placeholder[];
}

export function ChatInterface({
  conversation,
  onSendMessage,
  loading,
  placeholders = [],
}: ChatInterfaceProps) {
  const [input, setInput] = useState("");
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

  // Count filled fields
  const filled = placeholders.filter((p) => p.filled).length;
  const total = placeholders.length;
  const percentage = total > 0 ? (filled / total) * 100 : 0;

  return (
    <div className="chat-container">
      {/* Chat Header with Progress */}
      <div className="chat-header-bar">
        <div className="progress-info">
          <span className="progress-label">Progress:</span>
          <span className="progress-stat">
            {filled}/{total} fields filled
          </span>
          {total > 0 && (
            <div className="mini-progress-bar">
              <div
                className="mini-progress-fill"
                style={{ width: `${percentage}%` }}
              ></div>
            </div>
          )}
        </div>
      </div>

      {/* Messages */}
      <div className="messages">
        {conversation.length === 0 && (
          <div className="empty-state">
            <div className="empty-icon">👋</div>
            <p className="empty-text">Start by telling me about your document!</p>
          </div>
        )}

        {conversation.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-icon">
              {msg.role === "assistant" ? "🤖" : "👤"}
            </div>
            <div className="message-content">
              <div className="message-text">{msg.content}</div>
              <div className="message-time">
                {new Date().toLocaleTimeString([], {
                  hour: "2-digit",
                  minute: "2-digit",
                })}
              </div>
            </div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-icon">🤖</div>
            <div className="message-content">
              <div className="message-typing">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <div className="chat-footer">
        <form onSubmit={handleSubmit} className="chat-form">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Tell me the information... (e.g., 'The company is ABC Corp')"
            disabled={loading}
            className="chat-input"
            autoFocus
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="send-btn"
            title="Send message"
          >
            {loading ? (
              <span className="send-icon">⌛</span>
            ) : (
              <span className="send-icon">↑</span>
            )}
          </button>
        </form>
        <p className="chat-hint">
          💡 Tip: Provide information naturally, one field at a time or all
          together
        </p>
      </div>
    </div>
  );
}