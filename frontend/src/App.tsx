import React from "react";
import { FileUpload } from "./components/FileUpload";
import { ChatInterface } from "./components/ChatInterface";
import { PlaceholderList } from "./components/PlaceholderList";
import { ProgressBar } from "./components/ProgressBar";
import { useDocumentSession } from "./hooks/useDocumentSession";
import "./App.css";

function App() {
  const {
    sessionId,
    filename,
    placeholders,
    conversation,
    loading,
    error,
    uploadDocument,
    sendMessage,
    downloadDocument,
    resetSession,
  } = useDocumentSession();

  const isComplete = placeholders.length > 0 && placeholders.every((p) => p.filled);

  return (
    <div className="app">
      <header className="app-header">
        <h1>📋 Legal Document Assistant</h1>
        <p>Upload legal documents and fill placeholders with AI assistance</p>
      </header>

      {error && <div className="error-message">{error}</div>}

      {!sessionId ? (
        <main className="upload-container">
          <FileUpload onUpload={uploadDocument} loading={loading} />
        </main>
      ) : (
        <main className="workspace">
          <div className="left-panel">
            <PlaceholderList placeholders={placeholders} />
            <ProgressBar placeholders={placeholders} />
            <button
              className={`download-btn ${isComplete ? "active" : "disabled"}`}
              onClick={downloadDocument}
              disabled={!isComplete || loading}
            >
              {isComplete ? "📥 Download Completed Document" : "⏳ Fill remaining fields"}
            </button>
            <button className="reset-btn" onClick={resetSession}>
              ← Upload New Document
            </button>
          </div>

          <div className="right-panel">
            <ChatInterface
              conversation={conversation}
              onSendMessage={sendMessage}
              loading={loading}
            />
          </div>
        </main>
      )}
    </div>
  );
}

export default App;