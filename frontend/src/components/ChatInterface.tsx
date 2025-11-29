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

  return (
    <div className="chat-container">
      {/* Messages */}
      <div className="messages">
        {conversation.map((msg, idx) => (
          <div key={idx} className={`message ${msg.role}`}>
            <div className="message-icon">
              {msg.role === "assistant" ? "🤖" : "👤"}
            </div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}

        {loading && (
          <div className="message assistant">
            <div className="message-icon">🤖</div>
            <div className="message-content typing">
              <span></span>
              <span></span>
              <span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input form */}
      <form onSubmit={handleSubmit} className="chat-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Message..."
          disabled={loading}
          className="chat-input"
        />
        <button type="submit" disabled={loading || !input.trim()} className="send-btn">
          {loading ? "..." : "↑"}
        </button>
      </form>
    </div>
  );
}