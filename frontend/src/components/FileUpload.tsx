import React, { useState } from "react";

interface FileUploadProps {
  onUpload: (file: File) => Promise<void>;
  loading: boolean;
}

export function FileUpload({ onUpload, loading }: FileUploadProps) {
  const [dragActive, setDragActive] = useState(false);

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
      await onUpload(file);
    } else {
      alert("Please drop a .docx file");
    }
  };

  const handleChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files?.[0]) {
      await onUpload(e.target.files[0]);
    }
  };

  return (
    <div className="upload-wrapper">
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        className={`file-upload ${dragActive ? "active" : ""}`}
      >
        <div className="upload-content">
          <div className="upload-icon">📄</div>
          <h2>Upload Your Document</h2>
          <p className="upload-subtitle">Drag and drop your .docx file here</p>
          <div className="divider">or</div>
          <label className="file-input-label">
            <input
              type="file"
              accept=".docx"
              onChange={handleChange}
              disabled={loading}
              className="file-input"
            />
            <span className="file-input-button">
              {loading ? "Uploading..." : "Browse Files"}
            </span>
          </label>
          <p className="file-hint">Supported format: .docx</p>
        </div>
      </div>
    </div>
  );
}