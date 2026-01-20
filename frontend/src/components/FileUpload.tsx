import React, { useState } from "react";

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
}

export function FileUpload({ onUpload, loading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleDrag = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(e.type === "dragenter" || e.type === "dragover");
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith(".docx")) {
      setSelectedFile(file);
      await uploadFile(file);
    } else {
      alert("Please drop a .docx file");
    }
  };

  const uploadFile = async (file: File) => {
    // Simulate progress
    setUploadProgress(0);
    const progressInterval = setInterval(() => {
      setUploadProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return prev;
        }
        return prev + Math.random() * 30;
      });
    }, 200);

    try {
      await onUpload(file);
      setUploadProgress(100);
      clearInterval(progressInterval);
    } catch (error) {
      clearInterval(progressInterval);
      setUploadProgress(0);
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      setSelectedFile(e.target.files[0]);
      await uploadFile(e.target.files[0]);
    }
  };

  return (
    <div className="upload-wrapper">
      <div className="upload-container">
        {/* Header */}
        <div className="upload-header">
          <div className="upload-icon-large">📄</div>
          <h1>Legal Document Assistant</h1>
          <p className="upload-subtitle">
            Fill out your documents with AI assistance
          </p>
        </div>

        {/* Upload Area */}
        <div
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          className={`file-upload-area ${dragActive ? "active" : ""} ${
            loading ? "uploading" : ""
          }`}
        >
          {!loading && (
            <>
              <div className="upload-icon">✨</div>
              <h2>Upload Your Document</h2>
              <p className="upload-text">
                Drag and drop your .docx file here
              </p>

              <div className="upload-divider">
                <span>or</span>
              </div>

              <label className="file-input-label">
                <input
                  type="file"
                  accept=".docx"
                  onChange={handleChange}
                  disabled={loading}
                  className="file-input"
                />
                <span className="file-input-button">
                  <span className="button-icon">📁</span>
                  Choose File
                </span>
              </label>

              {selectedFile && (
                <div className="selected-file">
                  <span className="file-icon">📋</span>
                  <span className="file-name">{selectedFile.name}</span>
                </div>
              )}

              <p className="file-hint">
                <span className="hint-icon">ℹ️</span>
                Supported format: .docx files only (Max 50MB)
              </p>
            </>
          )}

          {loading && (
            <div className="upload-loading">
              <div className="loading-spinner"></div>
              <p className="loading-text">Processing your document...</p>
              <p className="loading-subtext">
                Extracting placeholders and inferring field types
              </p>
              <div className="progress-bar-upload">
                <div
                  className="progress-fill-upload"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
              <p className="progress-text">{Math.round(uploadProgress)}%</p>
            </div>
          )}
        </div>

        {/* Features */}
        <div className="upload-features">
          <div className="feature">
            <span className="feature-icon">🧠</span>
            <h3>Smart Detection</h3>
            <p>AI infers field types from document context</p>
          </div>
          <div className="feature">
            <span className="feature-icon">💬</span>
            <h3>Natural Chat</h3>
            <p>Fill fields by chatting naturally</p>
          </div>
          <div className="feature">
            <span className="feature-icon">⬇️</span>
            <h3>Export Ready</h3>
            <p>Download your completed document instantly</p>
          </div>
        </div>
      </div>
    </div>
  );
}