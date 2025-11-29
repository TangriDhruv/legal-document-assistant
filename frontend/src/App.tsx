import { useState } from "react";
import { FileUpload } from "./components/FileUpload";
import { ChatInterface } from "./components/ChatInterface";
import { useDocumentSession } from "./hooks/useDocumentSession";
import "./App.css";

function App() {
  const {
    sessionId,
    placeholders,
    conversation,
    loading,
    error,
    uploadDocument,
    sendMessage,
    downloadDocument,
    resetSession,
  } = useDocumentSession();

  const [sidebarOpen, setSidebarOpen] = useState(true);

  const isComplete = placeholders.length > 0 && placeholders.every((p) => p.filled);
  const filled = placeholders.filter((p) => p.filled).length;
  const total = placeholders.length;

  return (
    <div className="app">
      {error && <div className="error-message">{error}</div>}

      {!sessionId ? (
        // Upload screen
        <div className="upload-page">
          <FileUpload onUpload={uploadDocument} loading={loading} />
        </div>
      ) : (
        // Chat page with sidebar
        <div className="chat-page">
          {/* Sidebar */}
          <aside className={`sidebar ${sidebarOpen ? "open" : "closed"}`}>
            <div className="sidebar-header">
              <h2>📄 {placeholders.length > 0 ? "Document Fields" : "Document"}</h2>
              <button
                className="sidebar-close-btn"
                onClick={() => setSidebarOpen(false)}
                title="Close sidebar"
              >
                ✕
              </button>
            </div>

            <div className="sidebar-content">
              {placeholders.length > 0 && (
                <div className="sidebar-section">
                  {/* Progress */}
                  <div className="progress-section">
                    <div className="progress-stat">
                      <span className="progress-label">Completed</span>
                      <span className="progress-number">{filled}/{total}</span>
                    </div>
                    <div className="progress-bar-container">
                      <div 
                        className="progress-bar-fill" 
                        style={{ width: `${total > 0 ? (filled / total) * 100 : 0}%` }}
                      />
                    </div>
                  </div>

                  {/* Completed Fields */}
                  {filled > 0 && (
                    <div className="field-group">
                      <h4 className="field-group-title">✓ Completed ({filled})</h4>
                      <ul className="field-list">
                        {placeholders.filter((p) => p.filled).map((p) => (
                          <li key={p.name} className="field-item filled">
                            <div className="field-item-name">{p.name}</div>
                            <div className="field-item-value">{p.value}</div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Remaining Fields */}
                  {placeholders.filter((p) => !p.filled).length > 0 && (
                    <div className="field-group">
                      <h4 className="field-group-title">⏳ Remaining ({total - filled})</h4>
                      <ul className="field-list">
                        {placeholders.filter((p) => !p.filled).map((p) => (
                          <li key={p.name} className="field-item">
                            <div className="field-item-name">{p.name}</div>
                            {p.description && (
                              <div className="field-item-desc">{p.description}</div>
                            )}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="sidebar-footer">
              <button
                className={`download-btn ${isComplete ? "active" : "disabled"}`}
                onClick={downloadDocument}
                disabled={!isComplete || loading}
                title={isComplete ? "Download completed document" : "Fill all fields first"}
              >
                ⬇ Download
              </button>
              <button
                className="reset-btn"
                onClick={resetSession}
                title="Start with a new document"
              >
                ↺ New Document
              </button>
            </div>
          </aside>

          {/* Main Chat Area */}
          <main className="main-content">
            {/* Sidebar toggle button */}
            {!sidebarOpen && (
              <button
                className="sidebar-toggle"
                onClick={() => setSidebarOpen(true)}
                title="Open sidebar"
              >
                ☰
              </button>
            )}

            {/* Chat Interface */}
            <ChatInterface
              conversation={conversation}
              onSendMessage={sendMessage}
              loading={loading}
              placeholders={placeholders}
            />
          </main>
        </div>
      )}
    </div>
  );
}

export default App;