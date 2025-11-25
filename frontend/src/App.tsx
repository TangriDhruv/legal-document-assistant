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
      {/* Sidebar */}
      {sessionId && (
        <aside className={`sidebar ${!sidebarOpen ? "collapsed" : ""}`}>
          <div className="sidebar-header">
            <h2>{placeholders.length > 0 ? "Document Fields" : "Document"}</h2>
          </div>
          <div className="sidebar-content">
            {placeholders.length > 0 && (
              <div className="sidebar-section">
                <div className="sidebar-section-title">Fields ({filled}/{total})</div>
                {placeholders.map((p) => (
                  <div
                    key={p.name}
                    className={`sidebar-item ${p.filled ? "filled" : ""}`}
                  >
                    <div style={{ fontWeight: "500", fontSize: "0.9rem" }}>
                      {p.name}
                    </div>
                    {p.filled && (
                      <div style={{ fontSize: "0.8rem", marginTop: "0.25rem", opacity: 0.7, color: "#86efac" }}>
                        {p.value}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="sidebar-footer">
            {total > 0 && (
              <div className="progress-info">
                <span>{filled}/{total} completed</span>
              </div>
            )}
            <button
              className={`download-btn ${isComplete ? "active" : "disabled"}`}
              onClick={downloadDocument}
              disabled={!isComplete || loading}
            >
              Download
            </button>
            <button
              className="reset-btn"
              onClick={resetSession}
              style={{ marginTop: "0.75rem" }}
            >
              New Document
            </button>
          </div>
        </aside>
      )}

      <main>
        {sessionId && (
          <button
            className="sidebar-toggle"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            title={sidebarOpen ? "Hide sidebar" : "Show sidebar"}
          >
            {sidebarOpen ? "←" : "→"}
          </button>
        )}

        {error && <div className="error-message">{error}</div>}

        {!sessionId ? (
          <FileUpload onUpload={uploadDocument} loading={loading} />
        ) : (
          <div className="workspace">
            <ChatInterface
              conversation={conversation}
              onSendMessage={sendMessage}
              loading={loading}
              placeholders={placeholders}
            />
          </div>
        )}
      </main>
    </div>
  );
}

export default App;