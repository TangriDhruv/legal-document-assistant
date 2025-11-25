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
        <p>Drag and drop your .docx file here, or click to browse</p>
        <input
          type="file"
          accept=".docx"
          onChange={handleChange}
          disabled={loading}
          className="file-input"
        />
      </div>
    </div>
  );
}